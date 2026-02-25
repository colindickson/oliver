"""API routes for the Day resource.

Provides endpoints to retrieve today's day (with auto-creation), look up a
specific calendar date, and list all recorded days.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.daily_note import DailyNoteResponse, DailyNoteUpsert
from app.schemas.day import DayResponse
from app.schemas.day_metadata import DayMetadataResponse, DayMetadataUpsert
from app.schemas.day_rating import DayRatingResponse, DayRatingUpsert
from app.schemas.roadblock import RoadblockResponse, RoadblockUpsert
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
    await db.commit()  # persist if a new Day was created
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
    day = await service.get_or_create_by_date(day_date)
    await db.commit()  # persist if a new Day was created
    return day


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


@router.put("/{day_id}/notes", response_model=DailyNoteResponse)
async def upsert_notes(
    day_id: int,
    payload: DailyNoteUpsert,
    db: AsyncSession = Depends(get_db),
) -> DailyNoteResponse:
    """Create or update the daily note for a day.

    Args:
        day_id: Primary key of the target Day.
        payload: Note content to save.
        db: Injected async database session.

    Returns:
        The saved DailyNoteResponse.
    """
    service = DayService(db)
    note = await service.upsert_notes(day_id, payload.content)
    await db.commit()
    return note


@router.put("/{day_id}/roadblocks", response_model=RoadblockResponse)
async def upsert_roadblocks(
    day_id: int,
    payload: RoadblockUpsert,
    db: AsyncSession = Depends(get_db),
) -> RoadblockResponse:
    """Create or update the roadblock entry for a day.

    Args:
        day_id: Primary key of the target Day.
        payload: Roadblock content to save.
        db: Injected async database session.

    Returns:
        The saved RoadblockResponse.
    """
    service = DayService(db)
    roadblock = await service.upsert_roadblocks(day_id, payload.content)
    await db.commit()
    return roadblock


@router.put("/{day_id}/rating", response_model=DayRatingResponse)
async def upsert_rating(
    day_id: int,
    payload: DayRatingUpsert,
    db: AsyncSession = Depends(get_db),
) -> DayRatingResponse:
    """Create or update the subjective ratings for a day.

    Args:
        day_id: Primary key of the target Day.
        payload: Rating values to save.
        db: Injected async database session.

    Returns:
        The saved DayRatingResponse.
    """
    service = DayService(db)
    rating = await service.upsert_rating(
        day_id, payload.focus, payload.energy, payload.satisfaction
    )
    await db.commit()
    return rating


@router.put("/{day_id}/metadata", response_model=DayMetadataResponse)
async def upsert_metadata(
    day_id: int,
    payload: DayMetadataUpsert,
    db: AsyncSession = Depends(get_db),
) -> DayMetadataResponse:
    """Create or update the environmental metadata for a day.

    Args:
        day_id: Primary key of the target Day.
        payload: Metadata values to save.
        db: Injected async database session.

    Returns:
        The saved DayMetadataResponse.
    """
    service = DayService(db)
    meta = await service.upsert_metadata(
        day_id, payload.temperature_c, payload.condition, payload.moon_phase
    )
    await db.commit()
    return meta
