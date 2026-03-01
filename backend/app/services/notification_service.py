"""Service layer for notification CRUD and query operations.

Single responsibility: all database operations that concern the
Notification model are performed here and nowhere else.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationService:
    """Encapsulates all notification-related database operations.

    Args:
        db: An open async SQLAlchemy session injected by the FastAPI
            dependency system.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, source: str, content: str) -> Notification:
        """Persist a new notification and return the hydrated ORM instance.

        Args:
            source: Identifier for the system or component creating the notification.
            content: Human-readable notification text.

        Returns:
            The newly created :class:`Notification` with its database-assigned id.
        """
        notification = Notification(
            source=source,
            content=content,
            is_read=False,
        )
        self._db.add(notification)
        await self._db.commit()
        await self._db.refresh(notification)
        return notification

    async def list_recent(self, limit: int = 5) -> list[Notification]:
        """Return the most recent notifications ordered by created_at descending.

        Args:
            limit: Maximum number of notifications to return (default 5).

        Returns:
            A list of :class:`Notification` instances, possibly empty.
        """
        result = await self._db.execute(
            select(Notification)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_unread(self) -> list[Notification]:
        """Return all unread notifications ordered by created_at descending.

        Returns:
            A list of unread :class:`Notification` instances, possibly empty.
        """
        result = await self._db.execute(
            select(Notification)
            .where(Notification.is_read == False)  # noqa: E712
            .order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

    async def mark_read(self, notification_id: int) -> Notification | None:
        """Set is_read to True for the given notification.

        Args:
            notification_id: Primary key of the notification to update.

        Returns:
            The updated :class:`Notification`, or ``None`` if not found.
        """
        result = await self._db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if notification:
            notification.is_read = True
            await self._db.commit()
            await self._db.refresh(notification)
        return notification
