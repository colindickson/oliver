"""Service layer for WorkLog domain logic."""

from __future__ import annotations

from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oliver_shared import MAX_TAGS_PER_TASK

from app.exceptions import InvalidOperationError, WorkLogNotFoundError
from app.models.day import Day
from app.models.work_log import WorkLog
from app.schemas.work_log import WorkLogCreate
from app.services.day_service import DayService
from app.services.tag_service import TagService


class WorkLogService:
    """Encapsulates all WorkLog-related queries and write operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_day_id(self, day_id: int) -> list[WorkLog]:
        """Return all WorkLog entries for the given day, ordered by created_at ASC.

        Args:
            day_id: Primary key of the parent Day.

        Returns:
            Ordered list of WorkLog instances.
        """
        result = await self._db.execute(
            select(WorkLog)
            .where(WorkLog.day_id == day_id)
            .order_by(WorkLog.created_at.asc())
        )
        return list(result.scalars().all())

    async def delete(self, work_log_id: int) -> None:
        result = await self._db.execute(
            select(WorkLog).where(WorkLog.id == work_log_id)
        )
        work_log = result.scalar_one_or_none()
        if work_log is None:
            raise WorkLogNotFoundError(work_log_id)
        await self._db.delete(work_log)
        await self._db.flush()

    async def update(
        self,
        work_log_id: int,
        project_name: str | None = None,
        description: str | None = None,
    ) -> WorkLog:
        result = await self._db.execute(
            select(WorkLog).where(WorkLog.id == work_log_id)
        )
        work_log = result.scalar_one_or_none()
        if work_log is None:
            raise WorkLogNotFoundError(work_log_id)
        if project_name is not None:
            work_log.project_name = project_name
        if description is not None:
            work_log.description = description
        await self._db.flush()
        await self._db.refresh(work_log)
        return work_log

    async def create_batch(self, entries: list[WorkLogCreate]) -> list[WorkLog]:
        # Upfront validation — fail fast before touching the DB
        for i, entry in enumerate(entries):
            if len(entry.tags) > MAX_TAGS_PER_TASK:
                raise InvalidOperationError(
                    f"Entry {i} ('{entry.project_name}'): max {MAX_TAGS_PER_TASK} tags allowed",
                    http_status_code=400,
                )

        day_service = DayService(self._db)
        tag_service = TagService(self._db)

        unique_dates: set[date_type] = {entry.date for entry in entries}
        date_to_day: dict[date_type, Day] = {}
        for d in unique_dates:
            date_to_day[d] = await day_service.get_or_create_by_date(d)

        work_logs: list[WorkLog] = []
        for entry in entries:
            wl = WorkLog(
                day_id=date_to_day[entry.date].id,
                project_name=entry.project_name,
                description=entry.description,
            )
            self._db.add(wl)
            await self._db.flush()
            if entry.tags:
                wl.tags = await tag_service.resolve_tags(entry.tags)
                await self._db.flush()
            await self._db.refresh(wl)
            work_logs.append(wl)

        return work_logs

    async def update_tags(self, work_log_id: int, tag_names: list[str]) -> WorkLog:
        """Replace the tags on a WorkLog with the given tag names.

        Args:
            work_log_id: Primary key of the WorkLog to update.
            tag_names: New list of tag names to apply.

        Returns:
            The updated WorkLog instance.

        Raises:
            InvalidOperationError: 404 if no WorkLog with ``work_log_id`` exists.
        """
        if len(tag_names) > MAX_TAGS_PER_TASK:
            raise InvalidOperationError(
                f"A work log may have at most {MAX_TAGS_PER_TASK} tags",
                http_status_code=400,
            )

        result = await self._db.execute(
            select(WorkLog).where(WorkLog.id == work_log_id)
        )
        work_log = result.scalar_one_or_none()
        if work_log is None:
            raise WorkLogNotFoundError(work_log_id)

        tag_objects = await TagService(self._db).resolve_tags(tag_names)
        work_log.tags = tag_objects
        await self._db.flush()
        await self._db.refresh(work_log)
        return work_log
