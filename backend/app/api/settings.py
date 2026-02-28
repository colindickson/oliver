"""API routes for application settings."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.day_service import DayService

router = APIRouter(prefix="/api/settings", tags=["settings"])

VALID_WEEKDAYS = frozenset(
    {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
)


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


@router.get("/timer-display", response_model=TimerDisplayResponse)
async def get_timer_display(
    db: AsyncSession = Depends(get_db),
) -> TimerDisplayResponse:
    """Return whether the focus timer should be displayed.

    Args:
        db: Injected async database session.

    Returns:
        A TimerDisplayResponse with the enabled boolean.
    """
    service = DayService(db)
    return TimerDisplayResponse(enabled=await service.get_timer_display())


@router.put("/timer-display", response_model=TimerDisplayResponse)
async def set_timer_display(
    payload: TimerDisplayUpdate,
    db: AsyncSession = Depends(get_db),
) -> TimerDisplayResponse:
    """Save the timer display preference.

    Args:
        payload: The enabled boolean to store.
        db: Injected async database session.

    Returns:
        A TimerDisplayResponse with the saved boolean.
    """
    service = DayService(db)
    enabled = await service.set_timer_display(payload.enabled)
    await db.commit()
    return TimerDisplayResponse(enabled=enabled)


@router.get("/recurring-days-off", response_model=RecurringDaysOffResponse)
async def get_recurring_days_off(
    db: AsyncSession = Depends(get_db),
) -> RecurringDaysOffResponse:
    """Return the configured recurring off weekdays.

    Args:
        db: Injected async database session.

    Returns:
        A RecurringDaysOffResponse with the list of weekday names.
    """
    service = DayService(db)
    days = await service.get_recurring_days_off()
    return RecurringDaysOffResponse(days=days)


@router.put("/recurring-days-off", response_model=RecurringDaysOffResponse)
async def set_recurring_days_off(
    payload: RecurringDaysOffUpsert,
    db: AsyncSession = Depends(get_db),
) -> RecurringDaysOffResponse:
    """Save the recurring off weekdays configuration.

    Args:
        payload: List of valid weekday names.
        db: Injected async database session.

    Returns:
        A RecurringDaysOffResponse with the saved list.
    """
    service = DayService(db)
    days = await service.set_recurring_days_off(payload.days)
    await db.commit()
    return RecurringDaysOffResponse(days=days)
