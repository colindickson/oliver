"""Task model — one of the daily items in the 3-3-3 Technique."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.tag import Tag, task_tags_table
from oliver_shared import (
    CATEGORY_DEEP_WORK,
    CATEGORY_MAINTENANCE,
    CATEGORY_SHORT_TASK,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)

if TYPE_CHECKING:
    from app.models.day import Day
    from app.models.reminder import Reminder
    from app.models.timer_session import TimerSession


class Task(Base):
    """A single 3-3-3 task belonging to one day.

    Attributes:
        id: Auto-increment primary key.
        day_id: Foreign key to ``days.id`` with cascade delete. Nullable — ``None`` means backlog task.
        category: One of ``deep_work``, ``short_task``, or ``maintenance``.
        title: Short human-readable title.
        description: Optional extended description.
        status: Lifecycle state — ``pending``, ``in_progress``, or ``completed``.
        order_index: Ordering within a category; lower values appear first.
        completed_at: UTC timestamp set when status transitions to completed.
        timer_sessions: All timer sessions logged for this task.
        reminders: All reminders scheduled for this task.
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    day_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("days.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    category: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default=STATUS_PENDING)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    day: Mapped[Day] = relationship("Day", back_populates="tasks")
    timer_sessions: Mapped[list[TimerSession]] = relationship(
        "TimerSession",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reminders: Mapped[list[Reminder]] = relationship(
        "Reminder",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    tags: Mapped[list[Tag]] = relationship(
        "Tag",
        secondary=task_tags_table,
        lazy="selectin",
    )
