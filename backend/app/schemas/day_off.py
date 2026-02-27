"""Pydantic schemas for DayOff request and response payloads."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

DayOffReason = Literal["weekend", "personal_day", "vacation", "holiday", "sick_day"]


class DayOffUpsert(BaseModel):
    """Payload for creating or updating a day-off record."""

    reason: DayOffReason
    note: Optional[str] = None


class DayOffResponse(BaseModel):
    """Serialised representation of a DayOff returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    day_id: int
    reason: str
    note: Optional[str] = None
