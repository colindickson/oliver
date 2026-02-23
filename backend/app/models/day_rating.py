"""DayRating model — subjective focus / energy / satisfaction scores for a day."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.day import Day


class DayRating(Base):
    """Stores subjective day ratings (focus, energy, satisfaction) per Day.

    Each dimension is a nullable integer 1-5 (null means not yet rated).

    Attributes:
        id: Auto-increment primary key.
        day_id: Foreign key to the parent Day (unique — one rating per day).
        focus: Focus score 1-5, or None.
        energy: Energy score 1-5, or None.
        satisfaction: Satisfaction score 1-5, or None.
        day: Back-reference to the parent Day.
    """

    __tablename__ = "day_ratings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    day_id: Mapped[int] = mapped_column(
        ForeignKey("days.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    focus: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    energy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    satisfaction: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    day: Mapped[Day] = relationship("Day", back_populates="rating")
