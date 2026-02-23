"""Task model — one of the nine daily items in the 3-3-3 method."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.day import Day
    from app.models.reminder import Reminder
    from app.models.timer_session import TimerSession

# Valid literals kept as module-level constants so they can be reused in
# Pydantic schemas and validation logic without duplication.
CATEGORY_DEEP_WORK = "deep_work"
CATEGORY_SHORT_TASK = "short_task"
CATEGORY_MAINTENANCE = "maintenance"

STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"


class Task(Base):
    """A single 3-3-3 task belonging to one day.

    Attributes:
        id: Auto-increment primary key.
        day_id: Foreign key to ``days.id`` with cascade delete.
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
    day_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("days.id", ondelete="CASCADE"),
        nullable=False,
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
