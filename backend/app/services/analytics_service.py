"""AnalyticsService — single-responsibility analytics queries.

All public methods accept no arguments beyond those needed for their specific
query, delegating all database interaction to the injected AsyncSession so the
service remains independently testable.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_note import DailyNote
from app.models.day import Day
from app.models.day_off import DayOff
from app.models.task import Task, STATUS_COMPLETED
from app.models.timer_session import TimerSession


class AnalyticsService:
    """Encapsulates all analytics queries against the Oliver database.

    Args:
        db: An open SQLAlchemy async session injected by the caller.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    async def get_summary(self, days: int = 30) -> dict:
        """Return aggregated task-completion statistics for a rolling window.

        Args:
            days: Number of calendar days to include, counting back from today
                (inclusive).  Defaults to 30.

        Returns:
            A dict with keys ``period_days``, ``total_days_tracked``,
            ``total_tasks``, ``completed_tasks``, and ``completion_rate_pct``.
        """
        today = date.today()
        cutoff = today - timedelta(days=days)

        # Subquery for day IDs that are marked as off — excluded from all metrics
        off_day_ids_subq = select(DayOff.day_id)

        # EXISTS subqueries for days with content (tasks or notes)
        has_tasks = select(1).where(Task.day_id == Day.id).exists()
        has_notes = select(1).where(DailyNote.day_id == Day.id).exists()

        # Count distinct days in window (exclude today, off days, and empty days)
        days_result = await self._db.execute(
            select(func.count(Day.id))
            .where(Day.date >= cutoff)
            .where(Day.date < today)
            .where(Day.id.not_in(off_day_ids_subq))
            .where(or_(has_tasks, has_notes))
        )
        total_days_tracked: int = days_result.scalar_one() or 0

        # Count all tasks whose day is within the window (excluding off days)
        total_result = await self._db.execute(
            select(func.count(Task.id))
            .join(Day, Task.day_id == Day.id)
            .where(Day.date >= cutoff)
            .where(Day.date < today)
            .where(Day.id.not_in(off_day_ids_subq))
        )
        total_tasks: int = total_result.scalar_one() or 0

        # Count completed tasks within the window (excluding off days)
        completed_result = await self._db.execute(
            select(func.count(Task.id))
            .join(Day, Task.day_id == Day.id)
            .where(Day.date >= cutoff)
            .where(Day.date < today)
            .where(Task.status == STATUS_COMPLETED)
            .where(Day.id.not_in(off_day_ids_subq))
        )
        completed_tasks: int = completed_result.scalar_one() or 0

        completion_rate_pct = (
            round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0.0
        )

        return {
            "period_days": days,
            "total_days_tracked": total_days_tracked,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate_pct": completion_rate_pct,
        }

    # ------------------------------------------------------------------
    # Streaks
    # ------------------------------------------------------------------

    async def get_streaks(self) -> dict:
        """Calculate current and longest consecutive all-complete weekday streaks.

        Weekends (Saturday and Sunday) are automatically skipped — a streak is
        not broken by the Friday-to-Monday gap.

        A day counts toward a streak if it has at least one task and every one
        of its tasks has ``status == 'completed'``.

        For the current streak, consecutive weekdays are counted backwards from
        the most recent weekday.  For the longest streak, the full history is
        scanned.

        Returns:
            A dict with keys ``current_streak`` and ``longest_streak``.
        """
        days_result = await self._db.execute(
            select(Day).order_by(Day.date.asc())
        )
        all_days = list(days_result.scalars().all())

        if not all_days:
            return {"current_streak": 0, "longest_streak": 0}

        today = date.today()

        # Build a set of complete weekday dates (weekends, today, and off days excluded).
        complete_dates: set[date] = set()
        for day in all_days:
            if day.date >= today:  # exclude today — it's in progress
                continue
            if day.date.weekday() >= 5:  # Saturday=5, Sunday=6
                continue
            if day.day_off is not None:  # exclude explicit off days
                continue
            tasks = day.tasks  # loaded via selectin
            if tasks and all(t.status == STATUS_COMPLETED for t in tasks):
                complete_dates.add(day.date)

        if not complete_dates:
            return {"current_streak": 0, "longest_streak": 0}

        def _prev_workday(d: date) -> date:
            d -= timedelta(days=1)
            while d.weekday() >= 5:
                d -= timedelta(days=1)
            return d

        def _next_workday(d: date) -> date:
            d += timedelta(days=1)
            while d.weekday() >= 5:
                d += timedelta(days=1)
            return d

        # Current streak: count backwards from the most recent completed weekday
        # (yesterday or earlier — today is excluded as it's still in progress)
        cursor = today - timedelta(days=1)
        while cursor.weekday() >= 5:
            cursor -= timedelta(days=1)
        current_streak = 0
        while cursor in complete_dates:
            current_streak += 1
            cursor = _prev_workday(cursor)

        # Longest streak: scan all complete dates sorted ascending
        sorted_dates = sorted(complete_dates)
        longest_streak = 0
        run = 1
        for i in range(1, len(sorted_dates)):
            prev, curr = sorted_dates[i - 1], sorted_dates[i]
            if _next_workday(prev) == curr:
                run += 1
            else:
                longest_streak = max(longest_streak, run)
                run = 1
        longest_streak = max(longest_streak, run)

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
        }

    # ------------------------------------------------------------------
    # Category time
    # ------------------------------------------------------------------

    async def get_category_time(self) -> dict:
        """Sum timer-session durations grouped by task category.

        Only categories that have at least one completed timer session are
        included in the result.

        Returns:
            A dict with key ``entries``, whose value is a list of dicts each
            containing ``category``, ``total_seconds``, and ``task_count``.
        """
        off_day_ids_subq = select(DayOff.day_id)

        result = await self._db.execute(
            select(
                Task.category,
                func.sum(TimerSession.duration_seconds).label("total_seconds"),
                func.count(func.distinct(Task.id)).label("task_count"),
            )
            .join(TimerSession, TimerSession.task_id == Task.id)
            .join(Day, Task.day_id == Day.id)
            .where(TimerSession.duration_seconds.is_not(None))
            .where(Day.id.not_in(off_day_ids_subq))
            .group_by(Task.category)
            .order_by(Task.category)
        )
        rows = result.all()

        entries = [
            {
                "category": row.category,
                "total_seconds": int(row.total_seconds),
                "task_count": int(row.task_count),
            }
            for row in rows
        ]

        return {"entries": entries}

    # ------------------------------------------------------------------
    # Today's deep work time
    # ------------------------------------------------------------------

    async def get_today_deep_work_time(self) -> dict:
        """Calculate total deep work time for today.

        Sums all timer session durations for deep_work tasks on today's date.

        Returns:
            A dict with keys ``total_seconds`` and ``goal_seconds``.
            goal_seconds is fixed at 10800 (3 hours).
        """
        today = date.today()

        # Find today's day record
        day_result = await self._db.execute(
            select(Day).where(Day.date == today)
        )
        day = day_result.scalar_one_or_none()

        if not day:
            return {"total_seconds": 0, "goal_seconds": 10800}

        # Sum all timer session durations for deep_work tasks on this day
        result = await self._db.execute(
            select(func.coalesce(func.sum(TimerSession.duration_seconds), 0))
            .join(Task, TimerSession.task_id == Task.id)
            .where(Task.day_id == day.id)
            .where(Task.category == "deep_work")
            .where(TimerSession.duration_seconds.is_not(None))
        )
        total_seconds = int(result.scalar_one() or 0)

        return {"total_seconds": total_seconds, "goal_seconds": 10800}
