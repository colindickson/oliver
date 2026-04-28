"""WorkLog model and work_log_tags association table."""

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.base import Base

# Association table — not a mapped class, just a plain Table object.
work_log_tags_table = Table(
    "work_log_tags",
    Base.metadata,
    Column("work_log_id", Integer, ForeignKey("work_logs.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class WorkLog(Base):
    """A work log entry recording time spent on a project for a given day."""

    __tablename__ = "work_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_id = Column(Integer, ForeignKey("days.id", ondelete="CASCADE"), nullable=False)
    project_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    log_type = Column(
        Enum("commit", "pr", "review", "research", name="log_type"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    tags = relationship("Tag", secondary=work_log_tags_table, lazy="selectin")
