"""Service layer for Day domain logic.

Single responsibility: retrieve and create Day records by calendar date.
All database interaction is delegated to the injected AsyncSession so that
the service itself remains independently testable.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_note import DailyNote
from app.models.day import Day
from app.models.day_metadata import DayMetadata
from app.models.day_off import DayOff
from app.models.day_rating import DayRating
from app.models.roadblock import Roadblock
from app.models.setting import Setting
from app.models.task_template import TaskTemplate, TemplateSchedule
from app.services.template_service import compute_next_run, TemplateService

RECURRING_DAYS_OFF_KEY = "recurring_days_off"
TIMER_DISPLAY_KEY = "timer_display"


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

        await self.apply_due_schedules(day, target_date)
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

    async def upsert_metadata(
        self,
        day_id: int,
        temperature_c: Optional[float],
        condition: Optional[str],
        moon_phase: Optional[str],
    ) -> DayMetadata:
        """Create or update the environmental metadata for the given day.

        Args:
            day_id: Primary key of the parent Day.
            temperature_c: Temperature in Celsius, or None.
            condition: Weather condition string, or None.
            moon_phase: Moon phase string, or None.

        Returns:
            The persisted DayMetadata instance.
        """
        meta = await self._db.scalar(
            select(DayMetadata).where(DayMetadata.day_id == day_id)
        )
        if meta:
            meta.temperature_c = temperature_c
            meta.condition = condition
            meta.moon_phase = moon_phase
        else:
            meta = DayMetadata(
                day_id=day_id,
                temperature_c=temperature_c,
                condition=condition,
                moon_phase=moon_phase,
            )
            self._db.add(meta)
        await self._db.flush()
        await self._db.refresh(meta)
        return meta

    async def upsert_day_off(
        self, day_id: int, reason: str, note: Optional[str]
    ) -> DayOff:
        """Create or update the day-off record for the given day.

        Args:
            day_id: Primary key of the parent Day.
            reason: Why the day is off (one of the valid DayOffReason literals).
            note: Optional free-text context, or None.

        Returns:
            The persisted DayOff instance.
        """
        day_off = await self._db.scalar(
            select(DayOff).where(DayOff.day_id == day_id)
        )
        if day_off:
            day_off.reason = reason
            day_off.note = note
        else:
            day_off = DayOff(day_id=day_id, reason=reason, note=note)
            self._db.add(day_off)
        await self._db.flush()
        await self._db.refresh(day_off)
        return day_off

    async def remove_day_off(self, day_id: int) -> None:
        """Delete the day-off record for the given day, if it exists.

        Args:
            day_id: Primary key of the parent Day.
        """
        day_off = await self._db.scalar(
            select(DayOff).where(DayOff.day_id == day_id)
        )
        if day_off:
            await self._db.delete(day_off)
            await self._db.flush()

    async def get_all_day_offs(self) -> list[DayOff]:
        """Return all DayOff records ordered by day_id descending.

        Returns:
            A list of DayOff instances.
        """
        result = await self._db.execute(
            select(DayOff).order_by(DayOff.day_id.desc())
        )
        return list(result.scalars().all())

    async def get_timer_display(self) -> bool:
        """Return whether the focus timer should be displayed.

        Returns:
            True (default) if the timer should be shown, False if hidden.
        """
        setting = await self._db.scalar(
            select(Setting).where(Setting.key == TIMER_DISPLAY_KEY)
        )
        if setting is None:
            return True
        return json.loads(setting.value)

    async def set_timer_display(self, enabled: bool) -> bool:
        """Save the timer display preference to settings.

        Args:
            enabled: Whether the timer should be displayed.

        Returns:
            The saved boolean value.
        """
        setting = await self._db.scalar(
            select(Setting).where(Setting.key == TIMER_DISPLAY_KEY)
        )
        if setting:
            setting.value = json.dumps(enabled)
        else:
            setting = Setting(key=TIMER_DISPLAY_KEY, value=json.dumps(enabled))
            self._db.add(setting)
        await self._db.flush()
        return enabled

    async def get_recurring_days_off(self) -> list[str]:
        """Return the list of recurring off weekday names from settings.

        Returns:
            A list of lowercase weekday names, or empty list if not set.
        """
        setting = await self._db.scalar(
            select(Setting).where(Setting.key == RECURRING_DAYS_OFF_KEY)
        )
        if setting is None:
            return []
        return json.loads(setting.value)

    async def set_recurring_days_off(self, days: list[str]) -> list[str]:
        """Save the recurring off weekday names to settings.

        Args:
            days: List of lowercase weekday names to store.

        Returns:
            The saved list of weekday names.
        """
        setting = await self._db.scalar(
            select(Setting).where(Setting.key == RECURRING_DAYS_OFF_KEY)
        )
        if setting:
            setting.value = json.dumps(days)
        else:
            setting = Setting(key=RECURRING_DAYS_OFF_KEY, value=json.dumps(days))
            self._db.add(setting)
        await self._db.flush()
        return days

    async def get_next_working_day(self, from_date: date | None = None) -> date:
        """Return the next working day after from_date, skipping recurring and individual days off.

        Args:
            from_date: Starting date; defaults to today if None.

        Returns:
            The first date after from_date that is not a recurring day off and
            has no individual DayOff record.
        """
        if from_date is None:
            from_date = date.today()
        recurring_off = await self.get_recurring_days_off()
        candidate = from_date + timedelta(days=1)
        for _ in range(60):  # safety cap
            if candidate.strftime("%A").lower() not in recurring_off:
                # Check individual day-off (only if a Day row already exists)
                day_off_exists = await self._db.scalar(
                    select(DayOff).join(Day).where(Day.date == candidate)
                )
                if not day_off_exists:
                    return candidate
            candidate += timedelta(days=1)
        return from_date + timedelta(days=1)  # unreachable fallback

    async def apply_due_schedules(self, day: Day, target_date: date) -> None:
        """Instantiate tasks for any schedules due on or before target_date.

        For each schedule with next_run_date <= target_date:
        - Creates a task if next_run_date == target_date AND day is not a day off
        - Always advances next_run_date past target_date (catches missed occurrences)
        Idempotent: once next_run_date advances past target_date, it won't re-match.
        """
        is_day_off = day.day_off is not None

        result = await self._db.execute(
            select(TemplateSchedule).where(TemplateSchedule.next_run_date <= target_date)
        )
        schedules = list(result.scalars().all())

        if not schedules:
            return

        template_service = TemplateService(self._db)

        for schedule in schedules:
            if schedule.next_run_date == target_date and not is_day_off:
                template = await self._db.get(TaskTemplate, schedule.template_id)
                if template and template.category:
                    # Templates with no category are silently skipped — the cursor
                    # still advances. To avoid lost occurrences, always set a category
                    # on templates before scheduling them.
                    await template_service.instantiate(
                        template=template,
                        day_id=day.id,
                        category_override=None,
                        flush_only=True,
                    )

            # Advance next_run_date until it is strictly past target_date.
            # Pass anchor_date.day so monthly schedules don't drift after short months.
            while schedule.next_run_date <= target_date:
                schedule.next_run_date = compute_next_run(
                    schedule.next_run_date, schedule.recurrence, schedule.anchor_date.day
                )

        await self._db.flush()  # commit is handled by the route handler (days.py)
