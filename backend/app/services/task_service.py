"""Service layer for Task domain orchestration logic."""

from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task, CATEGORY_DEEP_WORK
from app.models.day import Day
from oliver_shared import STATUS_COMPLETED, STATUS_PENDING, STATUS_ROLLED_FORWARD
from app.services.day_service import DayService
from app.services.tag_service import TagService


class TaskService:
    """Encapsulates task orchestration operations (continue_tomorrow, roll_forward)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def continue_tomorrow(self, task_id: int) -> Task:
        """Mark a deep work task completed and create a copy on tomorrow's working day.

        The original task is stamped completed. A new pending task is created
        for tomorrow with the same title, description, and tags.

        Args:
            task_id: Primary key of the Task to continue.

        Returns:
            The newly created Task for tomorrow.

        Raises:
            HTTPException: 404 if no Task with ``task_id`` exists.
            HTTPException: 422 if task is not a deep_work task.
        """
        # Fetch original task with tags already loaded
        result = await self._db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.category != CATEGORY_DEEP_WORK:
            raise HTTPException(
                status_code=422,
                detail="Only deep_work tasks can be continued tomorrow",
            )

        # Read tag names before any mutations (already loaded)
        tag_names = [tag.name for tag in task.tags]

        # Get or create the next working day
        day_service = DayService(self._db)
        next_day = await day_service.get_next_working_day()
        tomorrow_day = await day_service.get_or_create_by_date(next_day)

        # Mark original completed
        task.status = STATUS_COMPLETED
        task.completed_at = datetime.now(timezone.utc)

        # Resolve tag objects for the new task
        tag_service = TagService(self._db)
        tag_objects = await tag_service.resolve_tags(tag_names)

        # Create continuation task
        new_task = Task(
            day_id=tomorrow_day.id,
            category=CATEGORY_DEEP_WORK,
            title=task.title,
            description=task.description,
            status=STATUS_PENDING,
            order_index=0,
        )
        new_task.tags = tag_objects
        self._db.add(new_task)

        # Single commit: atomically marks original completed and creates the copy
        await self._db.commit()
        await self._db.refresh(new_task)
        return new_task

    async def roll_forward(self, task_id: int, target_date: date) -> Task:
        """Create a new task on a future date as a roll-forward of an incomplete task.

        The original task is left incomplete but marked as rolled_forward.
        The new task has ``rolled_from_task_id`` set, creating a traceable chain.

        Args:
            task_id: Primary key of the source Task to roll forward.
            target_date: The date to roll the task forward to (must be in the future).

        Returns:
            The newly created Task with rolled_from_task_id set.

        Raises:
            HTTPException: 404 if no Task with ``task_id`` exists.
            HTTPException: 422 if task is completed, already rolled, or target_date is not future.
        """
        # Fetch with roll relationships for validation
        result = await self._db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.rolled_from),
                selectinload(Task.rolled_to),
            )
        )
        task = result.scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status in (STATUS_COMPLETED, STATUS_ROLLED_FORWARD):
            raise HTTPException(
                status_code=422,
                detail="Cannot roll forward a completed or already-rolled task",
            )

        if task.rolled_to is not None:
            raise HTTPException(status_code=422, detail="Task has already been rolled forward")

        if target_date <= date.today():
            raise HTTPException(status_code=422, detail="target_date must be in the future")

        # Read tag names
        tag_names = [tag.name for tag in task.tags]

        # Get or create the target day
        day_service = DayService(self._db)
        target_day = await day_service.get_or_create_by_date(target_date)

        # Resolve tag objects for the new task
        tag_service = TagService(self._db)
        tag_objects = await tag_service.resolve_tags(tag_names)

        # Create the rolled-forward task
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

        # Mark original as rolled_forward
        task.status = STATUS_ROLLED_FORWARD

        await self._db.commit()
        await self._db.refresh(new_task)
        return new_task
