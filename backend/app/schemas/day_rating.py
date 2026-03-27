"""Pydantic schemas for DayRating request and response payloads."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DayRatingUpsert(BaseModel):
    """Payload for creating or updating the day rating.

    All dimensions are optional so partial updates are supported
    (e.g. only setting focus without touching energy/satisfaction).

    Attributes:
        focus: Focus score 1-5, or None to clear.
        energy: Energy score 1-5, or None to clear.
        satisfaction: Satisfaction score 1-5, or None to clear.
    """

    focus: Optional[int] = Field(default=None, ge=1, le=5)
    energy: Optional[int] = Field(default=None, ge=1, le=5)
    satisfaction: Optional[int] = Field(default=None, ge=1, le=5)


class DayRatingResponse(BaseModel):
    """Serialised representation of a DayRating returned by the API.

    Attributes:
        id: Primary key.
        day_id: Parent Day foreign key.
        focus: Focus score 1-5, or None.
        energy: Energy score 1-5, or None.
        satisfaction: Satisfaction score 1-5, or None.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    day_id: int
    focus: Optional[int]
    energy: Optional[int]
    satisfaction: Optional[int]
