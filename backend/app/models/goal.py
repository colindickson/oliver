"""Goal model and junction tables for the Goals feature."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.tag import Tag
    from app.models.task import Task

# Association table: goal ↔ tag (tasks pulled in automatically via tag membership)
goal_tags_table = Table(
    "goal_tags",
    Base.metadata,
    Column("goal_id", Integer, ForeignKey("goals.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

# Association table: goal ↔ task (directly linked tasks)
goal_tasks_table = Table(
    "goal_tasks",
    Base.metadata,
    Column("goal_id", Integer, ForeignKey("goals.id", ondelete="CASCADE"), primary_key=True),
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
)

STATUS_GOAL_ACTIVE = "active"
STATUS_GOAL_COMPLETED = "completed"


class Goal(Base):
    """A named objective spanning multiple days, tracking progress over tasks."""

    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default=STATUS_GOAL_ACTIVE)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    tags: Mapped[list[Tag]] = relationship(
        "Tag",
        secondary=goal_tags_table,
        lazy="selectin",
    )
    direct_tasks: Mapped[list[Task]] = relationship(
        "Task",
        secondary=goal_tasks_table,
        lazy="selectin",
    )
