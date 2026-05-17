"""Service layer for Task domain orchestration logic."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import InvalidOperationError, TaskNotFoundError
from app.models.task import Task
from app.services.day_service import DayService
from app.services.tag_service import TagService
from oliver_shared import STATUS_COMPLETED, STATUS_PENDING, STATUS_ROLLED_FORWARD


class TaskService:
    """Encapsulates task orchestration operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

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

        tag_service = TagService(self._db)
        tag_objects = await tag_service.resolve_tags(tag_names)

        new_task = Task(
            day_id=target_day.id,
            category=task.category,
            title=task.title,
            description=task.description,
            status=STATUS_PENDING,
            order_index=0,
            rolled_from_task_id=task.id,
        )
        new_task.tags = tag_objects
        self._db.add(new_task)

        await self._db.flush()
        await self._db.refresh(new_task)
        return task, new_task
