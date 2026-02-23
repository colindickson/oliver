"""Reminder model — a scheduled notification for a task."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.task import Task


class Reminder(Base):
    """A single reminder notification tied to a task.

    Attributes:
        id: Auto-increment primary key.
        task_id: Foreign key to ``tasks.id``.
        remind_at: UTC timestamp at which the reminder should fire.
        message: Human-readable reminder text.
        is_delivered: ``True`` once the notification has been dispatched.
    """

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    is_delivered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    task: Mapped[Task] = relationship("Task", back_populates="reminders")
