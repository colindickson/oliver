"""Tag model and task_tags association table for the many-to-many relationship."""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# Association table — not a mapped class, just a plain Table object.
task_tags_table = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    """A user-defined label that can be applied to multiple tasks."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
