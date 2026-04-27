"""Service layer for WorkLog domain logic."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oliver_shared import MAX_TAGS_PER_TASK

from app.exceptions import InvalidOperationError, WorkLogNotFoundError
from app.models.work_log import WorkLog
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
