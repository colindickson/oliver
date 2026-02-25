"""Pydantic schemas for DayMetadata request and response payloads."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

WeatherCondition = Literal[
    "sunny", "partly_cloudy", "cloudy", "rainy", "snowy", "stormy", "foggy"
]

MoonPhase = Literal[
    "new_moon", "waxing_crescent", "first_quarter", "waxing_gibbous",
    "full_moon", "waning_gibbous", "last_quarter", "waning_crescent",
]


class DayMetadataUpsert(BaseModel):
    """Payload for creating or updating day metadata.

    All fields are optional so callers can set only what they know.

    Attributes:
        temperature_c: Temperature in Celsius, or None to clear.
        condition: Weather condition string, or None to clear.
        moon_phase: Moon phase string, or None to clear.
    """

    temperature_c: Optional[float] = None
    condition: Optional[WeatherCondition] = None
    moon_phase: Optional[MoonPhase] = None


class DayMetadataResponse(BaseModel):
    """Serialised representation of DayMetadata returned by the API.

    Attributes:
        id: Primary key.
        day_id: Parent Day foreign key.
        temperature_c: Temperature in Celsius, or None.
        condition: Weather condition string, or None.
        moon_phase: Moon phase string, or None.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    day_id: int
    temperature_c: Optional[float]
    condition: Optional[str]
    moon_phase: Optional[str]
