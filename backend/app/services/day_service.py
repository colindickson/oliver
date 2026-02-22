"""Service layer for Day domain logic.

Single responsibility: retrieve and create Day records by calendar date.
All database interaction is delegated to the injected AsyncSession so that
the service itself remains independently testable.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.day import Day


class DayService:
    """Encapsulates all Day-related queries and write operations.

    Args:
        db: An open SQLAlchemy async session injected by the caller.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_or_create_today(self) -> Day:
        """Return the Day record for the current calendar date, creating it if absent.

        Returns:
            The persisted Day instance for today.
        """
        return await self.get_or_create_by_date(date.today())

    async def get_or_create_by_date(self, target_date: date) -> Day:
        """Return the Day record for ``target_date``, creating it if absent.

        Args:
            target_date: The calendar date to look up or create.

        Returns:
            The persisted Day instance for the given date.
        """
        result = await self._db.execute(select(Day).where(Day.date == target_date))
        day = result.scalar_one_or_none()
        if day is None:
            day = Day(date=target_date, created_at=datetime.now(timezone.utc))
            self._db.add(day)
            await self._db.commit()
            await self._db.refresh(day)
        return day

    async def get_by_date(self, target_date: date) -> Day | None:
        """Return the Day record for ``target_date`` or ``None`` if not found.

        Args:
            target_date: The calendar date to look up.

        Returns:
            The matching Day, or ``None``.
        """
        result = await self._db.execute(select(Day).where(Day.date == target_date))
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Day]:
        """Return all Day records ordered newest-first.

        Returns:
            A list of Day instances sorted by date descending.
        """
        result = await self._db.execute(select(Day).order_by(Day.date.desc()))
        return list(result.scalars().all())
