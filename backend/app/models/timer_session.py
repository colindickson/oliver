"""TimerSession model — a single focused-work interval for a task."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.task import Task


class TimerSession(Base):
    """Records one start/stop interval of a running timer against a task.

    Attributes:
        id: Auto-increment primary key.
        task_id: Foreign key to ``tasks.id``.
        started_at: UTC timestamp when the timer was started.
        ended_at: UTC timestamp when the timer was stopped; ``None`` while running.
        duration_seconds: Pre-computed duration for completed sessions; ``None``
            while the session is still active.
    """

    __tablename__ = "timer_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    task: Mapped[Task] = relationship("Task", back_populates="timer_sessions")
