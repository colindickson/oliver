"""API routes for the Day resource.

Provides endpoints to retrieve today's day (with auto-creation), look up a
specific calendar date, and list all recorded days.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.day import DayResponse
from app.services.day_service import DayService

router = APIRouter(prefix="/api/days", tags=["days"])


@router.get("/today", response_model=DayResponse)
async def get_today(db: AsyncSession = Depends(get_db)) -> DayResponse:
    """Return the Day record for today, creating one if it does not yet exist.

    Args:
        db: Injected async database session.

    Returns:
        The DayResponse for the current calendar date.
    """
    service = DayService(db)
    day = await service.get_or_create_today()
    return day


@router.get("/{day_date}", response_model=DayResponse)
async def get_day_by_date(
    day_date: date, db: AsyncSession = Depends(get_db)
) -> DayResponse:
    """Return the Day record for a specific calendar date, creating one if absent.

    Args:
        day_date: The date to look up, parsed from the URL path (YYYY-MM-DD).
        db: Injected async database session.

    Returns:
        The DayResponse for the requested date.
    """
    service = DayService(db)
    return await service.get_or_create_by_date(day_date)


@router.get("", response_model=list[DayResponse])
async def list_days(db: AsyncSession = Depends(get_db)) -> list[DayResponse]:
    """Return all Day records ordered newest-first.

    Args:
        db: Injected async database session.

    Returns:
        A list of DayResponse objects sorted by date descending.
    """
    service = DayService(db)
    return await service.get_all()
