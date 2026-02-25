from sqlalchemy import Column, Float, ForeignKey, Integer, String

from models.base import Base


class DayMetadata(Base):
    """Environmental metadata (weather, moon phase) for a single calendar day."""

    __tablename__ = "day_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_id = Column(Integer, ForeignKey("days.id", ondelete="CASCADE"), unique=True, nullable=False)
    temperature_c = Column(Float, nullable=True)
    condition = Column(String(50), nullable=True)
    moon_phase = Column(String(50), nullable=True)
