"""Service layer for Tag domain logic."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag, task_tags_table
from app.models.task import Task
from app.models.day import Day
from oliver_shared import STATUS_ROLLED_FORWARD, normalize_tag_name


class TagService:
    """Encapsulates all Tag-related queries and write operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_or_create_tag(self, name: str) -> Tag:
        """Return the Tag for ``name`` (normalised), creating it if absent."""
        normalised = normalize_tag_name(name)
        result = await self._db.execute(select(Tag).where(Tag.name == normalised))
        tag = result.scalar_one_or_none()
        if tag is None:
            tag = Tag(name=normalised)
            self._db.add(tag)
            await self._db.flush()
        return tag

    async def get_all_tags(self) -> list[tuple[Tag, int]]:
        """Return tags that have at least one associated non-rolled-forward task, with usage counts."""
        stmt = (
            select(Tag, func.count(task_tags_table.c.task_id).label("task_count"))
            .join(task_tags_table, Tag.id == task_tags_table.c.tag_id)
            .join(Task, Task.id == task_tags_table.c.task_id)
            .where(Task.status != STATUS_ROLLED_FORWARD)
            .group_by(Tag.id)
            .having(func.count(task_tags_table.c.task_id) > 0)
            .order_by(Tag.name)
        )
        result = await self._db.execute(stmt)
        return [(row.Tag, row.task_count) for row in result.all()]

    async def get_tasks_for_tag(self, tag_name: str) -> list[dict]:
        """Return tasks grouped by day date for a given tag name.

        Returns an empty list if the tag doesn't exist.
        Groups are sorted descending by date.
        """
        normalised = normalize_tag_name(tag_name)
        tag_result = await self._db.execute(select(Tag).where(Tag.name == normalised))
        tag = tag_result.scalar_one_or_none()
        if tag is None:
            return []

        stmt = (
            select(Task, Day.date)
            .join(task_tags_table, Task.id == task_tags_table.c.task_id)
            .outerjoin(Day, Task.day_id == Day.id)
            .where(task_tags_table.c.tag_id == tag.id)
            .where(Task.status != STATUS_ROLLED_FORWARD)
            .order_by(Day.date.desc().nulls_last())
        )
        rows = (await self._db.execute(stmt)).all()

        groups: dict[str, list[Task]] = {}
        for task, day_date in rows:
            date_str = day_date.isoformat() if day_date is not None else "backlog"
            groups.setdefault(date_str, []).append(task)

        return [{"date": date_str, "tasks": tasks} for date_str, tasks in groups.items()]
