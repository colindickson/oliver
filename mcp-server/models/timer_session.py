from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from models.base import Base


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

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    task = relationship("Task", back_populates="timer_sessions")
