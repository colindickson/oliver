"""Task model — one of the daily items in the 3-3-3 Technique."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

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


class Task(Base):
    """A single 3-3-3 task belonging to one day.

    Attributes:
        id: Auto-increment primary key.
        day_id: Foreign key to ``days.id`` with cascade delete. Nullable. A task is backlog (idle) when unfinished and
            day-less or on a day other than today; see ``backlog_condition``.
        category: One of ``deep_work``, ``short_task``, or ``maintenance``. Nullable for backlog tasks.
        title: Short human-readable title.
        description: Optional extended description.
        status: Lifecycle state — ``pending``, ``in_progress``, or ``completed``.
        order_index: Ordering within a category; lower values appear first.
        completed_at: UTC timestamp set when status transitions to completed.
        external_source: System the task came from (e.g. ``jira``), lowercase; set with ``external_id``.
        external_id: Ticket key in that system (e.g. ``POKA-123``), used to sync status back.
        reminders: All reminders scheduled for this task.
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rolled_from_task_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    day_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("days.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(10000), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default=STATUS_PENDING)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    rolled_from: Mapped[Task | None] = relationship(
        "Task",
        foreign_keys=[rolled_from_task_id],
        remote_side="Task.id",
        backref=backref("rolled_to", uselist=False),
    )

    day: Mapped[Day | None] = relationship("Day", back_populates="tasks")
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

    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_day_id_category", "day_id", "category"),
        Index("ix_tasks_external_ref", "external_source", "external_id"),
        CheckConstraint(
            "category IS NULL OR category IN ('deep_work', 'short_task', 'maintenance')",
            name="ck_tasks_category_valid",
        ),
        CheckConstraint("order_index >= 0", name="ck_tasks_order_index_nonneg"),
    )
