from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from models.base import Base
from models.tag import task_tags_table
from oliver_shared import (
    CATEGORY_DEEP_WORK,
    CATEGORY_MAINTENANCE,
    CATEGORY_SHORT_TASK,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)


class Task(Base):
    """A single 3-3-3 task belonging to one day.

    Attributes:
        id: Auto-increment primary key.
        day_id: Foreign key to ``days.id`` with cascade delete.
        category: One of ``deep_work``, ``short_task``, or ``maintenance``.
        title: Short human-readable title.
        description: Optional extended description.
        status: Lifecycle state -- ``pending``, ``in_progress``, or ``completed``.
        order_index: Ordering within a category; lower values appear first.
        completed_at: UTC timestamp set when status transitions to completed.
        timer_sessions: All timer sessions logged for this task.
    """

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_id = Column(Integer, ForeignKey("days.id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False, default=STATUS_PENDING)
    order_index = Column(Integer, nullable=False, default=0)
    completed_at = Column(DateTime, nullable=True)

    day = relationship("Day", back_populates="tasks")
    timer_sessions = relationship(
        "TimerSession", back_populates="task", cascade="all, delete-orphan"
    )
    tags = relationship("Tag", secondary=task_tags_table, lazy="selectin")
