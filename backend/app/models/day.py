"""Day model — one row per calendar day."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.daily_note import DailyNote
    from app.models.day_metadata import DayMetadata
    from app.models.day_rating import DayRating
    from app.models.roadblock import Roadblock


class Day(Base):
    """Represents a single calendar day in the 3-3-3 plan.

    Attributes:
        id: Auto-increment primary key.
        date: The calendar date this row represents (unique).
        created_at: UTC timestamp when the row was first inserted.
        tasks: All tasks associated with this day.
        notes: Optional free-form notes for the day.
        roadblocks: Optional roadblock notes for the day.
        rating: Optional subjective ratings for the day.
        day_metadata: Optional environmental metadata (weather, moon phase).
    """

    __tablename__ = "days"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    tasks: Mapped[list[Task]] = relationship(  # noqa: F821
        "Task",
        back_populates="day",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    notes: Mapped[Optional[DailyNote]] = relationship(
        "DailyNote",
        back_populates="day",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    roadblocks: Mapped[Optional[Roadblock]] = relationship(
        "Roadblock",
        back_populates="day",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    rating: Mapped[Optional[DayRating]] = relationship(
        "DayRating",
        back_populates="day",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    day_metadata: Mapped[Optional[DayMetadata]] = relationship(
        "DayMetadata",
        back_populates="day",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_days_date", "date"),)
