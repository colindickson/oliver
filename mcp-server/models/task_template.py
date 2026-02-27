"""TaskTemplate model and template_tags association table (sync SQLAlchemy for MCP server)."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.sql import func

from models.base import Base
from models.tag import Tag  # noqa: F401 — ensures tags table is registered

template_tags_table = Table(
    "template_tags",
    Base.metadata,
    Column("template_id", Integer, ForeignKey("task_templates.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class TaskTemplate(Base):
    """A reusable task blueprint (sync model for MCP server)."""

    __tablename__ = "task_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
