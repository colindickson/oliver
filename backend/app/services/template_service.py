"""Service layer for TaskTemplate domain logic."""

from __future__ import annotations

from calendar import monthrange
from datetime import date as date_type, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.models.task import Task
from app.models.task_template import TaskTemplate
from app.services.tag_service import TagService
from oliver_shared import STATUS_PENDING, normalize_tag_name


def compute_next_run(current: date_type, recurrence: str) -> date_type:
    """Return the next occurrence date given the current date and recurrence type."""
    if recurrence == "weekly":
        return current + timedelta(days=7)
    if recurrence == "bi_weekly":
        return current + timedelta(days=14)
    # monthly: same day next month, clamped to last day of month
    month = current.month % 12 + 1
    year = current.year + (current.month // 12)
    max_day = monthrange(year, month)[1]
    return date_type(year, month, min(current.day, max_day))


class TemplateService:
    """Encapsulates all TaskTemplate queries and write operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_templates(self, search: str | None = None) -> list[TaskTemplate]:
        """Return all templates, optionally filtered by title substring."""
        stmt = select(TaskTemplate).order_by(TaskTemplate.title)
        if search:
            stmt = stmt.where(TaskTemplate.title.ilike(f"%{search}%"))
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_template(self, template_id: int) -> TaskTemplate | None:
        """Return a single template by ID, or None if not found."""
        result = await self._db.execute(
            select(TaskTemplate).where(TaskTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def create_template(
        self,
        title: str,
        description: str | None,
        category: str | None,
        tag_names: list[str],
    ) -> TaskTemplate:
        """Create and persist a new TaskTemplate."""
        tag_service = TagService(self._db)
        tag_objects = [await tag_service.get_or_create_tag(name) for name in tag_names]

        template = TaskTemplate(
            title=title,
            description=description,
            category=category,
        )
        template.tags = tag_objects
        self._db.add(template)
        await self._db.commit()
        await self._db.refresh(template)
        return template

    async def update_template(
        self,
        template: TaskTemplate,
        title: str | None,
        description: str | None,
        category: str | None,
        tag_names: list[str] | None,
    ) -> TaskTemplate:
        """Apply partial updates to an existing template."""
        if title is not None:
            template.title = title
        if description is not None:
            template.description = description
        if category is not None:
            template.category = category
        if tag_names is not None:
            tag_service = TagService(self._db)
            template.tags = [await tag_service.get_or_create_tag(n) for n in tag_names]

        await self._db.commit()
        await self._db.refresh(template)
        return template

    async def delete_template(self, template: TaskTemplate) -> None:
        """Delete a template."""
        await self._db.delete(template)
        await self._db.commit()

    async def instantiate(
        self,
        template: TaskTemplate,
        day_id: int,
        category_override: str | None,
        *,
        flush_only: bool = False,
    ) -> Task:
        """Create a Task from a template.

        Uses category_override if provided, else template.category.
        Raises ValueError if no category is available.
        Places the task at the end of its category column.

        Args:
            flush_only: If True, flush instead of commit (for callers that manage
                their own transaction, e.g. apply_due_schedules).
        """
        category = category_override if category_override is not None else template.category
        if category is None:
            raise ValueError("category is required: provide it in the request or set one on the template")

        # Compute order_index = count of tasks in this day+category
        count_result = await self._db.execute(
            select(func.count()).where(Task.day_id == day_id, Task.category == category)
        )
        order_index = count_result.scalar_one()

        # Copy tag objects from template
        tag_service = TagService(self._db)
        tag_objects = [await tag_service.get_or_create_tag(tag.name) for tag in template.tags]

        task = Task(
            day_id=day_id,
            category=category,
            title=template.title,
            description=template.description,
            status=STATUS_PENDING,
            order_index=order_index,
        )
        task.tags = tag_objects
        self._db.add(task)
        if flush_only:
            await self._db.flush()
        else:
            await self._db.commit()
            await self._db.refresh(task)
        return task

    async def list_schedules(self, template_id: int) -> "list[TemplateSchedule]":
        """Return all schedules for a template."""
        from app.models.task_template import TemplateSchedule
        result = await self._db.execute(
            select(TemplateSchedule).where(TemplateSchedule.template_id == template_id)
        )
        return list(result.scalars().all())

    async def create_schedule(
        self,
        template_id: int,
        recurrence: str,
        anchor_date: date_type,
    ) -> "TemplateSchedule":
        """Create a new recurrence schedule for a template."""
        from app.models.task_template import TemplateSchedule
        schedule = TemplateSchedule(
            template_id=template_id,
            recurrence=recurrence,
            anchor_date=anchor_date,
            next_run_date=anchor_date,
        )
        self._db.add(schedule)
        await self._db.commit()
        await self._db.refresh(schedule)
        return schedule

    async def delete_schedule(self, template_id: int, schedule_id: int) -> bool:
        """Delete a schedule by ID. Returns True if found and deleted."""
        from app.models.task_template import TemplateSchedule
        schedule = await self._db.scalar(
            select(TemplateSchedule).where(
                TemplateSchedule.id == schedule_id,
                TemplateSchedule.template_id == template_id,
            )
        )
        if schedule is None:
            return False
        await self._db.delete(schedule)
        await self._db.commit()
        return True
