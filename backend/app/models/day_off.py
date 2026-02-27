"""DayOff model — marks a day as an off day with a reason."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.day import Day


class DayOff(Base):
    """Records that a day is an off day (weekend, sick day, vacation, etc.).

    Attributes:
        id: Auto-increment primary key.
        day_id: Foreign key to the parent Day (unique — one record per day).
        reason: Why the day is off (validated by Pydantic Literal).
        note: Optional free-text context for the off day.
        day: Back-reference to the parent Day.
    """

    __tablename__ = "day_offs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    day_id: Mapped[int] = mapped_column(
        ForeignKey("days.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    reason: Mapped[str] = mapped_column(String(50), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    day: Mapped[Day] = relationship("Day", back_populates="day_off")
