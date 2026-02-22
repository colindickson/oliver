"""Day model — one row per calendar day."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Day(Base):
    """Represents a single calendar day in the 3-3-3 plan.

    Attributes:
        id: Auto-increment primary key.
        date: The calendar date this row represents (unique).
        created_at: UTC timestamp when the row was first inserted.
        tasks: All tasks associated with this day.
    """

    __tablename__ = "days"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    tasks: Mapped[list[Task]] = relationship(  # noqa: F821
        "Task",
        back_populates="day",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (Index("ix_days_date", "date"),)
