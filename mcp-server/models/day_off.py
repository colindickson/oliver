from sqlalchemy import Column, ForeignKey, Integer, String, Text

from models.base import Base


class DayOff(Base):
    """Records that a day is an off day (weekend, sick day, vacation, etc.)."""

    __tablename__ = "day_offs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_id = Column(Integer, ForeignKey("days.id", ondelete="CASCADE"), unique=True, nullable=False)
    reason = Column(String(50), nullable=False)
    note = Column(Text, nullable=True)
