from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Integer
from sqlalchemy.orm import relationship

from models.base import Base


class Day(Base):
    """Represents a single calendar day in the 3-3-3 plan.

    Attributes:
        id: Auto-increment primary key.
        date: The calendar date this row represents (unique).
        created_at: UTC timestamp when the row was first inserted.
        tasks: All tasks associated with this day.
    """

    __tablename__ = "days"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="day", cascade="all, delete-orphan")
