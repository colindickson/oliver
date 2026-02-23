from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text

from models.base import Base


class DailyNote(Base):
    """Free-form notes for a single calendar day."""

    __tablename__ = "daily_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_id = Column(Integer, ForeignKey("days.id", ondelete="CASCADE"), unique=True, nullable=False)
    content = Column(Text, nullable=False, default="")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
