"""Roadblock model — free-form roadblock notes for a single calendar day."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.day import Day


class Roadblock(Base):
    """Stores roadblock notes for a given Day (one row per day).

    Attributes:
        id: Auto-increment primary key.
        day_id: Foreign key to the parent Day (unique — one entry per day).
        content: The roadblock description text.
        updated_at: UTC timestamp of the last save.
        day: Back-reference to the parent Day.
    """

    __tablename__ = "roadblocks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    day_id: Mapped[int] = mapped_column(
        ForeignKey("days.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    day: Mapped[Day] = relationship("Day", back_populates="roadblocks")
