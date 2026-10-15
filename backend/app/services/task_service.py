"""Service layer for Task domain orchestration logic."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import and_, exists, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.exceptions import DayNotFoundError, InvalidOperationError, TaskNotFoundError
from app.models.day import Day
from app.models.goal import goal_tasks_table
from app.models.task import Task
from app.services.day_service import DayService
from app.services.tag_service import TagService
from app.services.timer_service import TimerService
from oliver_shared import (
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    STATUS_ROLLED_FORWARD,
)


def backlog_condition(today: date):
    """The one definition of the backlog: unfinished work that is idle.

    Idle means no day or any day other than ``today``, and not already continued
    (a pending continuation supersedes its original). Needs ``days`` outer-joined
    only if the caller wants the date; the predicate itself uses a subquery.
    """
    continuation = aliased(Task)
    return and_(
        Task.status.in_((STATUS_PENDING, STATUS_IN_PROGRESS)),
        or_(
            Task.day_id.is_(None),
            Task.day_id.in_(select(Day.id).where(Day.date != today)),
        ),
        ~exists().where(continuation.rolled_from_task_id == Task.id),
    )


class TaskService:
    """Encapsulates task orchestration operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def complete_stale(self, days: int) -> int:
        """Mark idle tasks scheduled on a day more than ``days`` ago as completed.

        Day-less tasks are deliberate backlog and are never touched.

        Returns:
            Number of tasks completed.
        """
        today = date.today()
        ids = (
            await self._db.execute(
                select(Task.id)
                .join(Day, Task.day_id == Day.id)
                .where(backlog_condition(today), Day.date < today - timedelta(days=days))
            )
        ).scalars().all()
        if ids:
            await self._db.execute(
                update(Task)
                .where(Task.id.in_(ids))
                .values(status=STATUS_COMPLETED, completed_at=datetime.now(timezone.utc))
            )
        return len(ids)

    async def continue_task(
        self, task_id: int, target_date: date | None = None
    ) -> tuple[Task, Task]:
        """Mark a task completed and schedule a continuation on a target day.

        Args:
            task_id: Primary key of the Task to continue.
            target_date: Optional future date for the new task; defaults to next working day.

        Returns:
            Tuple of (original_task, new_task).

        Raises:
            TaskNotFoundError: 404 if no Task with ``task_id`` exists.
            InvalidOperationError: 422 if task is in a terminal state or already continued.
            InvalidOperationError: 400 if ``target_date`` is not strictly in the future.
        """
        result = await self._db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(selectinload(Task.rolled_to))
            .with_for_update()
        )
        task = result.scalar_one_or_none()
        if task is None:
            raise TaskNotFoundError(task_id)

        if task.status in (STATUS_COMPLETED, STATUS_ROLLED_FORWARD):
            raise InvalidOperationError("Task is already in a terminal state")

        if task.rolled_to is not None:
            raise InvalidOperationError("Task has already been continued")

        if target_date is not None and target_date <= date.today():
            raise InvalidOperationError("target_date must be in the future", http_status_code=400)

        tag_names = [tag.name for tag in task.tags]

        day_service = DayService(self._db)
        if target_date is None:
            target_date = await day_service.get_next_working_day()
        target_day = await day_service.get_or_create_by_date(target_date)

        task.status = STATUS_COMPLETED
        task.completed_at = datetime.now(timezone.utc)

        new_task = await self._create_continuation(task, target_day.id, task.category, tag_names)
        return task, new_task

    async def _create_continuation(
        self, task: Task, target_day_id: int, category: str, tag_names: list[str]
    ) -> Task:
        """Copy ``task`` onto a day as a pending continuation, keeping direct goal links."""
        tag_objects = await TagService(self._db).resolve_tags(tag_names)

        new_task = Task(
            day_id=target_day_id,
            category=category,
            title=task.title,
            description=task.description,
            status=STATUS_PENDING,
            order_index=0,
            rolled_from_task_id=task.id,
        )
        new_task.tags = tag_objects
        self._db.add(new_task)
        await self._db.flush()

        goal_ids = (
            await self._db.execute(
                select(goal_tasks_table.c.goal_id).where(goal_tasks_table.c.task_id == task.id)
            )
        ).scalars().all()
        if goal_ids:
            await self._db.execute(
                insert(goal_tasks_table),
                [{"goal_id": g, "task_id": new_task.id} for g in goal_ids],
            )

        await self._db.refresh(new_task)
        return new_task

    async def schedule_to_day(self, task_id: int, day_id: int, category: str | None) -> Task:
        """Put an idle task on a day: move it, or roll a past-day task forward.

        Day-less and future tasks are moved (same row). A task on a past day is
        copied to the target day and the original becomes ``rolled_forward`` so
        past-day history and analytics are never rewritten.

        Raises:
            TaskNotFoundError: 404 if the task does not exist.
            DayNotFoundError: 404 if the target day does not exist.
            InvalidOperationError: 422 if terminal or already continued; 400 if the
                target is before today for a past-day task, or no category resolves.
        """
        result = await self._db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(selectinload(Task.rolled_to), selectinload(Task.day))
            .with_for_update()
        )
        task = result.scalar_one_or_none()
        if task is None:
            raise TaskNotFoundError(task_id)

        target_day = await self._db.get(Day, day_id)
        if target_day is None:
            raise DayNotFoundError(day_id)

        if task.day_id == day_id:
            return task

        if task.status in (STATUS_COMPLETED, STATUS_ROLLED_FORWARD):
            raise InvalidOperationError("Task is already in a terminal state")
        if task.rolled_to is not None:
            raise InvalidOperationError("Task has already been continued")

        category = category or task.category
        if category is None:
            raise InvalidOperationError("Category is required", http_status_code=400)

        today = date.today()
        if task.day is None or task.day.date >= today:
            task.day_id = day_id  # column only: setting Day.tasks would delete-orphan
            task.category = category
            return task

        if target_day.date < today:
            raise InvalidOperationError(
                "Cannot roll a past-day task onto a past day", http_status_code=400
            )
        tag_names = [tag.name for tag in task.tags]
        task.status = STATUS_ROLLED_FORWARD
        new_task = await self._create_continuation(task, day_id, category, tag_names)
        await TimerService(self._db).reassign(task.id, new_task.id)
        return new_task

    async def move_task_category(
        self, task_id: int, new_category: str, order_index: int | None = None
    ) -> Task:
        result = await self._db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(selectinload(Task.tags))
            .with_for_update()
        )
        task = result.scalar_one_or_none()
        if task is None:
            raise TaskNotFoundError(task_id)

        if task.day_id is None:
            raise InvalidOperationError(
                "Task must be on a day to move between categories"
            )

        if task.category == new_category:
            if order_index is not None:
                task.order_index = order_index
            return task

        day_id = task.day_id
        old_category = task.category

        if order_index is None:
            count_result = await self._db.execute(
                select(Task).where(Task.day_id == day_id, Task.category == new_category)
            )
            task.order_index = len(count_result.scalars().all())
        else:
            task.order_index = order_index

        task.category = new_category

        await self._db.flush()

        src_result = await self._db.execute(
            select(Task)
            .where(Task.day_id == day_id, Task.category == old_category)
            .order_by(Task.order_index)
        )
        for i, t in enumerate(src_result.scalars().all()):
            t.order_index = i

        dest_result = await self._db.execute(
            select(Task)
            .where(Task.day_id == day_id, Task.category == new_category)
            .order_by(Task.order_index)
        )
        for i, t in enumerate(dest_result.scalars().all()):
            t.order_index = i

        await self._db.flush()
        await self._db.refresh(task)
        return task
