"""API routes for the Backlog resource.

The backlog is idle work: unfinished tasks with no day or on any day other than
today (see ``backlog_condition``). Tasks can be created, listed, and scheduled
onto a day.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.tasks import build_task_response
from app.database import get_db
from app.models.day import Day
from app.models.task import Task
from app.schemas.task import (
    BacklogTaskCreate,
    MoveToDayPayload,
    TaskResponse,
)
from app.services.tag_service import TagService
from app.services.task_service import TaskService, backlog_condition

router = APIRouter(prefix="/api/backlog", tags=["backlog"])


@router.get("", response_model=list[TaskResponse])
async def list_backlog(
    tag: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[TaskResponse]:
    """Return all idle tasks, optionally filtered.

    Args:
        tag: Filter by tag name.
        search: Fuzzy search on title (case-insensitive contains).
        db: Injected async database session.

    Returns:
        Idle tasks with ``day_date`` set: day-less first, then past days
        most-recent-first, then future days soonest-first.
    """
    today = date.today()
    query = (
        select(Task, Day.date)
        .outerjoin(Day, Task.day_id == Day.id)
        .where(backlog_condition(today))
    )

    if tag:
        query = query.where(Task.tags.any(name=tag.lower()))

    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.where(Task.title.ilike(f"%{escaped}%", escape="\\"))

    query = query.order_by(
        Task.day_id.isnot(None),
        case((Day.date < today, 0), else_=1),
        case((Day.date < today, Day.date)).desc(),
        Day.date.asc(),
        Task.order_index,
        Task.id,
    )
    result = await db.execute(query)
    return [
        TaskResponse.model_validate(task).model_copy(update={"day_date": day_date})
        for task, day_date in result.all()
    ]


@router.post("", response_model=TaskResponse, status_code=201)
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
    service = TagService(db)
    tag_objects = await service.resolve_tags(body.tags)

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


@router.post("/complete-stale")
async def complete_stale_backlog_tasks(
    days: int = Query(7, ge=1), db: AsyncSession = Depends(get_db)
) -> dict[str, int]:
    """Mark idle tasks scheduled more than ``days`` days ago as done.

    Clears work that was put on a daily board and never closed out.

    Returns:
        ``{"completed": <count>}``.
    """
    completed = await TaskService(db).complete_stale(days)
    await db.commit()
    return {"completed": completed}


@router.post("/{task_id}/move-to-day", response_model=TaskResponse)
async def move_backlog_task_to_day(
    task_id: int,
    body: MoveToDayPayload,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Schedule an idle task onto a day (move it, or roll a past-day task forward).

    Args:
        task_id: Primary key of the task.
        body: Contains day_id and optional category override.
        db: Injected async database session.

    Returns:
        The task now on the day (a new copy when rolled forward from a past day).

    Raises:
        HTTPException: 404 task/day not found; 422 terminal or already continued;
            400 no category, or past-day task targeted at a past day.
    """
    task = await TaskService(db).schedule_to_day(task_id, body.day_id, body.category)
    await db.commit()

    result = await db.execute(
        select(Task)
        .where(Task.id == task.id)
        .options(
            selectinload(Task.rolled_from).selectinload(Task.day),
            selectinload(Task.rolled_to).selectinload(Task.day),
        )
    )
    return build_task_response(result.scalar_one())
