"""Service layer for Day domain logic.

Single responsibility: retrieve and create Day records by calendar date.
All database interaction is delegated to the injected AsyncSession so that
the service itself remains independently testable.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_note import DailyNote
from app.models.day import Day
from app.models.day_rating import DayRating
from app.models.roadblock import Roadblock


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
            await self._db.flush()
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

    async def upsert_notes(self, day_id: int, content: str) -> DailyNote:
        """Create or update the daily note for the given day.

        Args:
            day_id: Primary key of the parent Day.
            content: Note text to save.

        Returns:
            The persisted DailyNote instance.
        """
        note = await self._db.scalar(
            select(DailyNote).where(DailyNote.day_id == day_id)
        )
        if note:
            note.content = content
            note.updated_at = datetime.now(timezone.utc)
        else:
            note = DailyNote(
                day_id=day_id,
                content=content,
                updated_at=datetime.now(timezone.utc),
            )
            self._db.add(note)
        await self._db.flush()
        await self._db.refresh(note)
        return note

    async def upsert_roadblocks(self, day_id: int, content: str) -> Roadblock:
        """Create or update the roadblock entry for the given day.

        Args:
            day_id: Primary key of the parent Day.
            content: Roadblock text to save.

        Returns:
            The persisted Roadblock instance.
        """
        roadblock = await self._db.scalar(
            select(Roadblock).where(Roadblock.day_id == day_id)
        )
        if roadblock:
            roadblock.content = content
            roadblock.updated_at = datetime.now(timezone.utc)
        else:
            roadblock = Roadblock(
                day_id=day_id,
                content=content,
                updated_at=datetime.now(timezone.utc),
            )
            self._db.add(roadblock)
        await self._db.flush()
        await self._db.refresh(roadblock)
        return roadblock

    async def upsert_rating(
        self,
        day_id: int,
        focus: Optional[int],
        energy: Optional[int],
        satisfaction: Optional[int],
    ) -> DayRating:
        """Create or update the subjective ratings for the given day.

        Args:
            day_id: Primary key of the parent Day.
            focus: Focus score 1-5, or None.
            energy: Energy score 1-5, or None.
            satisfaction: Satisfaction score 1-5, or None.

        Returns:
            The persisted DayRating instance.
        """
        rating = await self._db.scalar(
            select(DayRating).where(DayRating.day_id == day_id)
        )
        if rating:
            rating.focus = focus
            rating.energy = energy
            rating.satisfaction = satisfaction
        else:
            rating = DayRating(
                day_id=day_id,
                focus=focus,
                energy=energy,
                satisfaction=satisfaction,
            )
            self._db.add(rating)
        await self._db.flush()
        await self._db.refresh(rating)
        return rating
