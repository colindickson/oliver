"""Pydantic schemas for Day request and response payloads."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.daily_note import DailyNoteResponse
from app.schemas.day_metadata import DayMetadataResponse
from app.schemas.day_off import DayOffResponse
from app.schemas.day_rating import DayRatingResponse
from app.schemas.roadblock import RoadblockResponse
from app.schemas.task import TaskResponse


class DayResponse(BaseModel):
    """Serialised representation of a Day returned by the API.

    Attributes:
        id: Primary key.
        date: The calendar date this record represents.
        created_at: UTC timestamp of row creation.
        tasks: All tasks associated with this day.
        notes: Optional free-form notes for the day.
        roadblocks: Optional roadblock notes for the day.
        rating: Optional subjective ratings for the day.
        day_metadata: Optional environmental metadata (weather, moon phase).
        day_off: Optional day-off record if the day is marked as off.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    created_at: datetime
    tasks: list[TaskResponse] = []
    notes: Optional[DailyNoteResponse] = None
    roadblocks: Optional[RoadblockResponse] = None
    rating: Optional[DayRatingResponse] = None
    day_metadata: Optional[DayMetadataResponse] = None
    day_off: Optional[DayOffResponse] = None
