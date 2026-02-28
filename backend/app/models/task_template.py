"""TaskTemplate model and template_tags association table."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.tag import Tag

template_tags_table = Table(
    "template_tags",
    Base.metadata,
    Column("template_id", Integer, ForeignKey("task_templates.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class TaskTemplate(Base):
    """A reusable task blueprint that can be instantiated into a real Task."""

    __tablename__ = "task_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tags: Mapped[list[Tag]] = relationship(
        "Tag",
        secondary=template_tags_table,
        lazy="selectin",
    )
    schedules: Mapped[list["TemplateSchedule"]] = relationship(
        "TemplateSchedule",
        back_populates="template",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class TemplateSchedule(Base):
    """A recurring schedule attached to a TaskTemplate."""

    __tablename__ = "template_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("task_templates.id", ondelete="CASCADE"), nullable=False
    )
    recurrence: Mapped[str] = mapped_column(String(20), nullable=False)  # weekly | bi_weekly | monthly
    anchor_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_run_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    template: Mapped["TaskTemplate"] = relationship("TaskTemplate", back_populates="schedules")
