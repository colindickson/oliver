"""TimerService — encapsulates timer state machine operations.

The active timer state is persisted as a JSON blob in the ``settings`` table
under the key ``"active_timer"``, which avoids the need for any server-side
process or background thread beyond what already exists in the database.

State machine:
    idle -> running -> paused -> running -> idle
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting
from app.models.timer_session import TimerSession

TIMER_KEY = "active_timer"


class TimerService:
    """Single-responsibility service for timer state transitions.

    Args:
        db: An open async SQLAlchemy session injected per request.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Private state helpers
    # ------------------------------------------------------------------

    async def _get_state(self) -> dict | None:
        """Read raw timer state from the settings table.

        Returns:
            Parsed JSON dict if an active timer exists, otherwise ``None``.
        """
        result = await self._db.execute(
            select(Setting).where(Setting.key == TIMER_KEY)
        )
        setting = result.scalar_one_or_none()
        if setting is None:
            return None
        return json.loads(setting.value)

    async def _set_state(self, state: dict) -> None:
        """Persist timer state to the settings table.

        Args:
            state: Dict to serialise and store under ``TIMER_KEY``.
        """
        result = await self._db.execute(
            select(Setting).where(Setting.key == TIMER_KEY)
        )
        setting = result.scalar_one_or_none()
        if setting is None:
            setting = Setting(key=TIMER_KEY, value=json.dumps(state))
            self._db.add(setting)
        else:
            setting.value = json.dumps(state)
        await self._db.commit()

    async def _clear_state(self) -> None:
        """Remove the active timer entry from the settings table."""
        result = await self._db.execute(
            select(Setting).where(Setting.key == TIMER_KEY)
        )
        setting = result.scalar_one_or_none()
        if setting:
            await self._db.delete(setting)
            await self._db.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_current(self) -> dict:
        """Return current timer state with live elapsed_seconds computed.

        Returns:
            A dict with keys ``status``, ``task_id``, ``elapsed_seconds``,
            and ``accumulated_seconds``.
        """
        state = await self._get_state()
        if state is None:
            return {
                "status": "idle",
                "task_id": None,
                "elapsed_seconds": 0,
                "accumulated_seconds": 0,
            }

        accumulated = state.get("accumulated_seconds", 0)
        if state["status"] == "running":
            started_at = datetime.fromisoformat(state["started_at"])
            interval = int((datetime.now(timezone.utc) - started_at).total_seconds())
            elapsed = accumulated + interval
        else:
            elapsed = accumulated

        return {
            "status": state["status"],
            "task_id": state["task_id"],
            "elapsed_seconds": elapsed,
            "accumulated_seconds": accumulated,
        }

    async def start(self, task_id: int) -> dict:
        """Start or resume the timer for a task.

        If a paused timer exists for the same ``task_id``, it is resumed and
        its accumulated seconds are carried forward.  If a timer is already
        running (for any task), a ``ValueError`` is raised.

        Args:
            task_id: Primary key of the Task to start timing.

        Returns:
            Current timer state dict (same shape as ``get_current``).

        Raises:
            ValueError: If a timer is already in the running state.
        """
        state = await self._get_state()
        now = datetime.now(timezone.utc)

        if state is not None and state["status"] == "running":
            raise ValueError("Timer is already running")

        accumulated = 0
        if (
            state is not None
            and state["status"] == "paused"
            and state["task_id"] == task_id
        ):
            accumulated = state.get("accumulated_seconds", 0)

        await self._set_state(
            {
                "task_id": task_id,
                "status": "running",
                "started_at": now.isoformat(),
                "accumulated_seconds": accumulated,
            }
        )
        return await self.get_current()

    async def pause(self) -> dict:
        """Pause the currently running timer.

        Calculates the elapsed interval since ``started_at`` and folds it into
        ``accumulated_seconds``.

        Returns:
            Current timer state dict with ``status == "paused"``.

        Raises:
            ValueError: If no timer is currently running.
        """
        state = await self._get_state()
        if state is None or state["status"] != "running":
            raise ValueError("No timer is currently running")

        started_at = datetime.fromisoformat(state["started_at"])
        interval = int((datetime.now(timezone.utc) - started_at).total_seconds())
        accumulated = state.get("accumulated_seconds", 0) + interval

        await self._set_state(
            {
                "task_id": state["task_id"],
                "status": "paused",
                "accumulated_seconds": accumulated,
            }
        )
        return await self.get_current()

    async def stop(self) -> TimerSession:
        """Stop the timer and persist a completed TimerSession record.

        Works from either the running or paused state.  The total duration
        is accumulated seconds plus any live interval (if running).

        Returns:
            The newly created and persisted ``TimerSession`` ORM instance.

        Raises:
            ValueError: If no active timer exists (idle state).
        """
        state = await self._get_state()
        if state is None:
            raise ValueError("No timer is currently running or paused")

        accumulated = state.get("accumulated_seconds", 0)
        now = datetime.now(timezone.utc)

        if state["status"] == "running":
            started_at = datetime.fromisoformat(state["started_at"])
            interval = int((now - started_at).total_seconds())
            total = accumulated + interval
            session_started_at = started_at
        else:
            total = accumulated
            session_started_at = now

        session = TimerSession(
            task_id=state["task_id"],
            started_at=session_started_at,
            ended_at=now,
            duration_seconds=total,
        )
        self._db.add(session)
        await self._db.commit()
        await self._db.refresh(session)
        await self._clear_state()
        return session

    async def get_sessions_for_task(self, task_id: int) -> list[TimerSession]:
        """Return all timer sessions for a given task, newest first.

        Args:
            task_id: Primary key of the Task whose sessions to retrieve.

        Returns:
            A list of ``TimerSession`` instances ordered by ``started_at`` desc.
        """
        result = await self._db.execute(
            select(TimerSession)
            .where(TimerSession.task_id == task_id)
            .order_by(TimerSession.started_at.desc())
        )
        return list(result.scalars().all())

    async def add_time(self, task_id: int, seconds: int) -> TimerSession:
        """Create a TimerSession record crediting manual time to a task.

        Does not interact with any active timer state.

        Args:
            task_id: Primary key of the Task to credit.
            seconds: Number of seconds to add.

        Returns:
            The newly created and persisted ``TimerSession`` ORM instance.
        """
        now = datetime.now(timezone.utc)
        session = TimerSession(
            task_id=task_id,
            started_at=now - timedelta(seconds=seconds),
            ended_at=now,
            duration_seconds=seconds,
        )
        self._db.add(session)
        await self._db.commit()
        await self._db.refresh(session)
        return session
