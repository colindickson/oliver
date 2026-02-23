from sqlalchemy import Column, ForeignKey, Integer

from models.base import Base


class DayRating(Base):
    """Subjective focus / energy / satisfaction scores for a single calendar day."""

    __tablename__ = "day_ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_id = Column(Integer, ForeignKey("days.id", ondelete="CASCADE"), unique=True, nullable=False)
    focus = Column(Integer, nullable=True)
    energy = Column(Integer, nullable=True)
    satisfaction = Column(Integer, nullable=True)
