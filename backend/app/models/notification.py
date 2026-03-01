"""Notification model — a system notification with no foreign-key dependencies."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Notification(Base):
    """A single notification entry.

    Attributes:
        id: Auto-increment primary key.
        source: Identifier for the system or component that created the notification.
        content: Human-readable notification text (max 500 characters).
        is_read: ``True`` once the notification has been acknowledged by the user.
        created_at: UTC timestamp when the notification was created.
    """

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
