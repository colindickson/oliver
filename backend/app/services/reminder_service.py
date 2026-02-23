"""Service layer for reminder CRUD and due-reminder queries.

Single responsibility: all database operations that concern the
Reminder model are performed here and nowhere else.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminder import Reminder


class ReminderService:
    """Encapsulates all reminder-related database operations.

    Args:
        db: An open async SQLAlchemy session injected by the FastAPI
            dependency system.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, task_id: int, remind_at: datetime, message: str) -> Reminder:
        """Persist a new reminder and return the hydrated ORM instance.

        Args:
            task_id: Primary key of the owning task.
            remind_at: UTC datetime when the reminder should fire.
            message: Human-readable notification text.

        Returns:
            The newly created :class:`Reminder` with its database-assigned id.
        """
        reminder = Reminder(
            task_id=task_id,
            remind_at=remind_at,
            message=message,
            is_delivered=False,
        )
        self._db.add(reminder)
        await self._db.commit()
        await self._db.refresh(reminder)
        return reminder

    async def list_for_task(self, task_id: int) -> list[Reminder]:
        """Return all reminders for a task ordered by remind_at ascending.

        Args:
            task_id: Primary key of the owning task.

        Returns:
            A list of :class:`Reminder` instances, possibly empty.
        """
        result = await self._db.execute(
            select(Reminder)
            .where(Reminder.task_id == task_id)
            .order_by(Reminder.remind_at)
        )
        return list(result.scalars().all())

    async def get_due(self) -> list[Reminder]:
        """Return all undelivered reminders where remind_at <= now (UTC).

        Returns:
            A list of :class:`Reminder` instances ordered by remind_at ascending.
        """
        now = datetime.now(timezone.utc)
        result = await self._db.execute(
            select(Reminder)
            .where(Reminder.remind_at <= now, Reminder.is_delivered == False)  # noqa: E712
            .order_by(Reminder.remind_at)
        )
        return list(result.scalars().all())

    async def mark_delivered(self, reminder_id: int) -> Reminder | None:
        """Set is_delivered to True for the given reminder.

        Args:
            reminder_id: Primary key of the reminder to update.

        Returns:
            The updated :class:`Reminder`, or ``None`` if not found.
        """
        result = await self._db.execute(
            select(Reminder).where(Reminder.id == reminder_id)
        )
        reminder = result.scalar_one_or_none()
        if reminder:
            reminder.is_delivered = True
            await self._db.commit()
            await self._db.refresh(reminder)
        return reminder

    async def delete(self, reminder_id: int) -> bool:
        """Delete a reminder by primary key.

        Args:
            reminder_id: Primary key of the reminder to delete.

        Returns:
            ``True`` if the reminder existed and was deleted, ``False`` otherwise.
        """
        result = await self._db.execute(
            select(Reminder).where(Reminder.id == reminder_id)
        )
        reminder = result.scalar_one_or_none()
        if reminder:
            await self._db.delete(reminder)
            await self._db.commit()
            return True
        return False
