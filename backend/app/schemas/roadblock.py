"""Pydantic schemas for Roadblock request and response payloads."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RoadblockUpsert(BaseModel):
    """Payload for creating or updating the roadblock entry for a day.

    Attributes:
        content: The roadblock description text to save.
    """

    content: str


class RoadblockResponse(BaseModel):
    """Serialised representation of a Roadblock returned by the API.

    Attributes:
        id: Primary key.
        day_id: Parent Day foreign key.
        content: The saved roadblock text.
        updated_at: UTC timestamp of the last save.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    day_id: int
    content: str
    updated_at: datetime
