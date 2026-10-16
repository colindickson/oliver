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
        day_id: Foreign key to ``days.id`` with cascade delete. Nullable; backlog membership is defined by the idle query, not by this alone.
        category: One of ``deep_work``, ``short_task``, or ``maintenance``. Nullable for backlog tasks.
        title: Short human-readable title.
        description: Optional extended description.
        status: Lifecycle state -- ``pending``, ``in_progress``, or ``completed``.
        order_index: Ordering within a category; lower values appear first.
        rolled_from_task_id: Original task this one continues; an original with a continuation is not idle.
        completed_at: UTC timestamp set when status transitions to completed.
        external_source: System the task came from (e.g. ``jira``), lowercase; set with ``external_id``.
        external_id: Ticket key in that system (e.g. ``POKA-123``), used to sync status back.
    """

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_id = Column(Integer, ForeignKey("days.id", ondelete="CASCADE"), nullable=True)
    category = Column(String, nullable=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False, default=STATUS_PENDING)
    order_index = Column(Integer, nullable=False, default=0)
    completed_at = Column(DateTime, nullable=True)
    rolled_from_task_id = Column(
        Integer, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    external_source = Column(String(50), nullable=True)
    external_id = Column(String(255), nullable=True)

    day = relationship("Day", back_populates="tasks")
    tags = relationship("Tag", secondary=task_tags_table, lazy="selectin")
