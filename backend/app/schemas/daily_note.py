"""Pydantic schemas for DailyNote request and response payloads."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DailyNoteUpsert(BaseModel):
    """Payload for creating or updating the daily note for a day.

    Attributes:
        content: The note text to save.
    """

    content: str


class DailyNoteResponse(BaseModel):
    """Serialised representation of a DailyNote returned by the API.

    Attributes:
        id: Primary key.
        day_id: Parent Day foreign key.
        content: The saved note text.
        updated_at: UTC timestamp of the last save.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    day_id: int
    content: str
    updated_at: datetime
