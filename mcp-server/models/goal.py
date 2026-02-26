"""Goal model and junction tables for the Goals feature (MCP server mirror)."""

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from models.base import Base

goal_tags_table = Table(
    "goal_tags",
    Base.metadata,
    Column("goal_id", Integer, ForeignKey("goals.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

goal_tasks_table = Table(
    "goal_tasks",
    Base.metadata,
    Column("goal_id", Integer, ForeignKey("goals.id", ondelete="CASCADE"), primary_key=True),
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
)


class Goal(Base):
    """A named objective spanning multiple days."""

    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    target_date = Column(Date, nullable=True)
    status = Column(String, nullable=False, default="active")
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)

    tags = relationship("Tag", secondary=goal_tags_table, lazy="selectin")
    direct_tasks = relationship("Task", secondary=goal_tasks_table, lazy="selectin")
