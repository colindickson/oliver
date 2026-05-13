"""Service layer for application settings.

Single responsibility: read and write key-value settings stored in the
Setting table. All database interaction is delegated to the injected
AsyncSession so that the service itself remains independently testable.
"""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting
from oliver_shared import FOCUS_GOAL_KEY, RECURRING_DAYS_OFF_KEY, TIMER_DISPLAY_KEY


class SettingsService:
    """Encapsulates all application-settings queries and write operations.

    Args:
        db: An open SQLAlchemy async session injected by the caller.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

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

    async def get_focus_goal_id(self) -> int | None:
        """Return the current focus goal ID, or None if not set.

        Returns:
            The focus goal ID, or None.
        """
        setting = await self._db.scalar(
            select(Setting).where(Setting.key == FOCUS_GOAL_KEY)
        )
        if setting is None:
            return None
        return json.loads(setting.value)

    async def set_focus_goal_id(self, goal_id: int | None) -> int | None:
        """Save the focus goal ID to settings.

        Args:
            goal_id: The goal ID to set as focus, or None to clear.

        Returns:
            The saved goal ID.
        """
        setting = await self._db.scalar(
            select(Setting).where(Setting.key == FOCUS_GOAL_KEY)
        )
        if setting:
            setting.value = json.dumps(goal_id)
        else:
            setting = Setting(key=FOCUS_GOAL_KEY, value=json.dumps(goal_id))
            self._db.add(setting)
        await self._db.flush()
        return goal_id

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
