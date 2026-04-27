"""WorkLog model — tracks work sessions with project and description."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.tag import Tag

if TYPE_CHECKING:
    from app.models.day import Day

# Association table — not a mapped class, just a plain Table object.
work_log_tags_table = Table(
    "work_log_tags",
    Base.metadata,
    Column("work_log_id", Integer, ForeignKey("work_logs.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_work_log_tags_tag_id", "tag_id"),
)


class WorkLog(Base):
    """A work log entry belonging to one day.

    Attributes:
        id: Auto-increment primary key.
        day_id: Foreign key to ``days.id`` with cascade delete. NOT nullable.
        project_name: Name of the project this work log is associated with.
        description: Extended description of work done.
        created_at: UTC timestamp set at row creation (DB-level default).
        day: The Day this work log belongs to.
        tags: Tags associated with this work log.
    """

    __tablename__ = "work_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    day_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("days.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    day: Mapped[Day] = relationship("Day", back_populates="work_logs")
    tags: Mapped[list[Tag]] = relationship(
        "Tag",
        secondary=work_log_tags_table,
        lazy="selectin",
    )
