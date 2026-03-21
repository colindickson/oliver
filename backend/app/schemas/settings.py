"""Pydantic schemas for settings endpoints."""

from __future__ import annotations

from pydantic import BaseModel, field_validator

from oliver_shared import VALID_WEEKDAYS


class RecurringDaysOffResponse(BaseModel):
    """Response schema for recurring days-off setting."""

    days: list[str]


class RecurringDaysOffUpsert(BaseModel):
    """Request schema for updating recurring days-off setting."""

    days: list[str]

    @field_validator("days")
    @classmethod
    def validate_weekday_names(cls, v: list[str]) -> list[str]:
        invalid = [d for d in v if d not in VALID_WEEKDAYS]
        if invalid:
            raise ValueError(
                f"Invalid weekday name(s): {invalid}. Must be one of: {sorted(VALID_WEEKDAYS)}"
            )
        return v


class TimerDisplayResponse(BaseModel):
    """Response schema for timer display setting."""

    enabled: bool


class TimerDisplayUpdate(BaseModel):
    """Request schema for updating timer display setting."""

    enabled: bool


class FocusGoalResponse(BaseModel):
    """Response schema for focus goal setting."""

    goal_id: int | None


class FocusGoalUpdate(BaseModel):
    """Request schema for updating focus goal setting."""

    goal_id: int | None
