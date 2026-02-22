"""Pydantic schemas for Day request and response payloads."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.task import TaskResponse


class DayResponse(BaseModel):
    """Serialised representation of a Day returned by the API.

    Attributes:
        id: Primary key.
        date: The calendar date this record represents.
        created_at: UTC timestamp of row creation.
        tasks: All tasks associated with this day.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    created_at: datetime
    tasks: list[TaskResponse] = []
