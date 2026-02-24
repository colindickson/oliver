"""API routes for the Backlog resource.

Backlog tasks are tasks without a day_id (day_id is null).
They can be created, listed, and moved to a specific day.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.day import Day
from app.models.task import Task
from app.schemas.task import (
    BacklogTaskCreate,
    MoveToDayPayload,
    TaskResponse,
)
from app.services.tag_service import TagService
from oliver_shared import MAX_TAGS_PER_TASK

router = APIRouter(prefix="/api/backlog", tags=["backlog"])


async def _get_backlog_task_or_404(task_id: int, db: AsyncSession) -> Task:
    """Fetch a backlog Task by primary key or raise 404.

    Args:
        task_id: The primary key to look up.
        db: Open async session.

    Returns:
        The matching Task instance.

    Raises:
        HTTPException: 404 if no backlog Task with ``task_id`` exists.
    """
    result = await db.execute(select(Task).where(Task.id == task_id, Task.day_id.is_(None)))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Backlog task not found")
    return task


@router.get("", response_model=list[TaskResponse])
async def list_backlog(
    tag: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[TaskResponse]:
    """Return all backlog tasks, optionally filtered.

    Args:
        tag: Filter by tag name.
        search: Fuzzy search on title (case-insensitive contains).
        db: Injected async database session.

    Returns:
        List of backlog tasks sorted by order_index.
    """
    query = select(Task).where(Task.day_id.is_(None))

    if tag:
        query = query.join(Task.tags).where(Task.tags.any(name=tag.lower()))

    if search:
        query = query.where(Task.title.ilike(f"%{search}%"))

    query = query.order_by(Task.order_index)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=TaskResponse)
async def create_backlog_task(
    body: BacklogTaskCreate, db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """Create a new backlog task (no day_id).

    Args:
        body: Backlog task creation payload.
        db: Injected async database session.

    Returns:
        The persisted TaskResponse.

    Raises:
        HTTPException: 400 if more than MAX_TAGS_PER_TASK tags are provided.
    """
    if len(body.tags) > MAX_TAGS_PER_TASK:
        raise HTTPException(status_code=400, detail=f"A task may have at most {MAX_TAGS_PER_TASK} tags")

    tag_objects = []
    if body.tags:
        service = TagService(db)
        for tag_name in body.tags:
            tag_objects.append(await service.get_or_create_tag(tag_name))

    task = Task(
        day_id=None,
        category=body.category,
        title=body.title,
        description=body.description,
        order_index=0,
    )
    task.tags = tag_objects
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.post("/{task_id}/move-to-day", response_model=TaskResponse)
async def move_backlog_task_to_day(
    task_id: int,
    body: MoveToDayPayload,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Move a backlog task to a specific day.

    Args:
        task_id: Primary key of the backlog task.
        body: Contains day_id and optional category override.
        db: Injected async database session.

    Returns:
        The updated TaskResponse.

    Raises:
        HTTPException: 404 if task or day not found.
        HTTPException: 400 if category is required but not provided.
    """
    task = await _get_backlog_task_or_404(task_id, db)

    # Verify day exists
    result = await db.execute(select(Day).where(Day.id == body.day_id))
    day = result.scalar_one_or_none()
    if day is None:
        raise HTTPException(status_code=404, detail="Day not found")

    # Determine category
    category = body.category or task.category
    if category is None:
        raise HTTPException(status_code=400, detail="Category is required")

    task.day_id = body.day_id
    task.category = category
    await db.commit()
    await db.refresh(task)
    return task
