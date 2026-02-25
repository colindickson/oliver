"""DayMetadata model — environmental context (weather, moon phase) for a day."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.day import Day


class DayMetadata(Base):
    """Stores environmental metadata (weather, moon phase) per Day.

    Enum values are validated at the Pydantic layer, not as Postgres ENUM types,
    to keep migrations simple and SQLite-compatible for tests.

    Attributes:
        id: Auto-increment primary key.
        day_id: Foreign key to the parent Day (unique — one metadata row per day).
        temperature_c: Temperature in Celsius, or None.
        condition: Weather condition string (validated by Pydantic Literal).
        moon_phase: Moon phase string (validated by Pydantic Literal).
        day: Back-reference to the parent Day.
    """

    __tablename__ = "day_metadata"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    day_id: Mapped[int] = mapped_column(
        ForeignKey("days.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    temperature_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    condition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    moon_phase: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    day: Mapped[Day] = relationship("Day", back_populates="day_metadata")
