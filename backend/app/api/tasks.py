"""API routes for the Task resource.

Provides full CRUD plus dedicated status-transition and bulk-reorder endpoints.
All database access uses async SQLAlchemy so the routes remain non-blocking.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task import Task
from app.schemas.task import (
    TaskCreate,
    TaskReorder,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.services.tag_service import TagService
from oliver_shared import MAX_TAGS_PER_TASK, STATUS_COMPLETED, validate_tag_count

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_task_or_404(task_id: int, db: AsyncSession) -> Task:
    """Fetch a Task by primary key or raise a 404 HTTPException.

    Args:
        task_id: The primary key to look up.
        db: Open async session.

    Returns:
        The matching Task instance.

    Raises:
        HTTPException: 404 if no Task with ``task_id`` exists.
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ---------------------------------------------------------------------------
# Reorder — must be declared BEFORE /{id} routes to avoid path ambiguity
# ---------------------------------------------------------------------------


@router.post("/reorder")
async def reorder_tasks(
    body: TaskReorder, db: AsyncSession = Depends(get_db)
) -> dict[str, bool]:
    """Bulk-update order_index for a list of tasks.

    The position of each task id within ``body.task_ids`` becomes its new
    ``order_index`` value (0-based).

    Args:
        body: Contains ``task_ids``, an ordered list of primary keys.
        db: Injected async database session.

    Returns:
        ``{"reordered": True}`` on success.
    """
    for new_index, task_id in enumerate(body.task_ids):
        task = await _get_task_or_404(task_id, db)
        task.order_index = new_index
    await db.commit()
    return {"reordered": True}


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.post("", response_model=TaskResponse)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)) -> TaskResponse:
    """Create a new Task associated with an existing Day.

    Args:
        body: Task creation payload.
        db: Injected async database session.

    Returns:
        The persisted TaskResponse.

    Raises:
        HTTPException: 400 if more than MAX_TAGS_PER_TASK tags are provided.
    """
    if len(body.tags) > MAX_TAGS_PER_TASK:
        raise HTTPException(status_code=400, detail=f"A task may have at most {MAX_TAGS_PER_TASK} tags")

    # Resolve tags before creating the task so we can set them on the
    # transient object — avoids a lazy-load in async context.
    tag_objects = []
    if body.tags:
        service = TagService(db)
        for tag_name in body.tags:
            tag_objects.append(await service.get_or_create_tag(tag_name))

    task = Task(
        day_id=body.day_id,
        category=body.category,
        title=body.title,
        description=body.description,
        order_index=body.order_index,
    )
    task.tags = tag_objects  # set on transient — no DB load required
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    day_id: int | None = None, db: AsyncSession = Depends(get_db)
) -> list[TaskResponse]:
    """Return tasks, optionally filtered by day.

    Args:
        day_id: When provided, only tasks belonging to this Day are returned.
        db: Injected async database session.

    Returns:
        A list of TaskResponse objects.
    """
    query = select(Task)
    if day_id is not None:
        query = query.where(Task.day_id == day_id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)) -> TaskResponse:
    """Return a single Task by primary key.

    Args:
        task_id: The primary key of the desired Task.
        db: Injected async database session.

    Returns:
        The matching TaskResponse.

    Raises:
        HTTPException: 404 if no Task with ``task_id`` exists.
    """
    return await _get_task_or_404(task_id, db)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int, body: TaskUpdate, db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """Update mutable fields on an existing Task.

    Only non-None fields in the payload are applied, preserving unchanged
    values. ``body.tags = None`` means don't touch tags; ``body.tags = []``
    removes all tags.

    Args:
        task_id: Primary key of the Task to update.
        body: Partial or full update payload.
        db: Injected async database session.

    Returns:
        The updated TaskResponse.

    Raises:
        HTTPException: 404 if no Task with ``task_id`` exists.
        HTTPException: 400 if more than MAX_TAGS_PER_TASK tags are provided.
    """
    task = await _get_task_or_404(task_id, db)
    if body.title is not None:
        task.title = body.title
    if body.description is not None:
        task.description = body.description
    if body.order_index is not None:
        task.order_index = body.order_index

    if body.tags is not None:
        if len(body.tags) > MAX_TAGS_PER_TASK:
            raise HTTPException(status_code=400, detail=f"A task may have at most {MAX_TAGS_PER_TASK} tags")
        new_tag_objects = []
        if body.tags:
            service = TagService(db)
            for tag_name in body.tags:
                new_tag_objects.append(await service.get_or_create_tag(tag_name))
        task.tags = new_tag_objects

    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: int, db: AsyncSession = Depends(get_db)
) -> dict[str, bool]:
    """Delete a Task by primary key.

    Args:
        task_id: Primary key of the Task to remove.
        db: Injected async database session.

    Returns:
        ``{"deleted": True}`` on success.

    Raises:
        HTTPException: 404 if no Task with ``task_id`` exists.
    """
    task = await _get_task_or_404(task_id, db)
    await db.delete(task)
    await db.commit()
    return {"deleted": True}


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: int, body: TaskStatusUpdate, db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """Transition a Task to a new lifecycle status.

    When the status is set to ``completed``, ``completed_at`` is stamped with
    the current UTC time.

    Args:
        task_id: Primary key of the Task to update.
        body: Contains the desired ``status`` value.
        db: Injected async database session.

    Returns:
        The updated TaskResponse.

    Raises:
        HTTPException: 404 if no Task with ``task_id`` exists.
    """
    task = await _get_task_or_404(task_id, db)
    task.status = body.status
    if body.status == STATUS_COMPLETED:
        task.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    return task


@router.post("/{task_id}/move-to-backlog", response_model=TaskResponse)
async def move_task_to_backlog(
    task_id: int, db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """Move a task from a day back to the backlog.

    Sets day_id and category to null, preserving other fields.

    Args:
        task_id: Primary key of the Task to move.
        db: Injected async database session.

    Returns:
        The updated TaskResponse.

    Raises:
        HTTPException: 404 if no Task with ``task_id`` exists.
    """
    task = await _get_task_or_404(task_id, db)
    task.day_id = None
    task.category = None
    await db.commit()
    await db.refresh(task)
    return task
