"""API routes for application settings."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.goal import Goal
from app.schemas.settings import (
    FocusGoalResponse,
    FocusGoalUpdate,
    RecurringDaysOffResponse,
    RecurringDaysOffUpsert,
    TimerDisplayResponse,
    TimerDisplayUpdate,
)
from app.services.day_service import DayService

router = APIRouter(prefix="/api/settings", tags=["settings"])


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


@router.get("/focus-goal", response_model=FocusGoalResponse)
async def get_focus_goal(
    db: AsyncSession = Depends(get_db),
) -> FocusGoalResponse:
    """Return the current focus goal ID.

    Args:
        db: Injected async database session.

    Returns:
        A FocusGoalResponse with the goal_id (or null if not set).
    """
    service = DayService(db)
    goal_id = await service.get_focus_goal_id()
    return FocusGoalResponse(goal_id=goal_id)


@router.put("/focus-goal", response_model=FocusGoalResponse)
async def set_focus_goal(
    payload: FocusGoalUpdate,
    db: AsyncSession = Depends(get_db),
) -> FocusGoalResponse:
    """Save the focus goal preference.

    Args:
        payload: The goal_id to set as focus, or null to clear.
        db: Injected async database session.

    Returns:
        A FocusGoalResponse with the saved goal_id.
    """
    service = DayService(db)
    if payload.goal_id is not None:
        goal = await db.scalar(select(Goal).where(Goal.id == payload.goal_id))
        if goal is None:
            raise HTTPException(status_code=404, detail="Goal not found")
        if goal.archived_at is not None:
            raise HTTPException(status_code=400, detail="Cannot set an archived goal as focus goal")
    goal_id = await service.set_focus_goal_id(payload.goal_id)
    await db.commit()
    return FocusGoalResponse(goal_id=goal_id)


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
