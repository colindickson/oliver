"""API routes for the Day resource.

Provides endpoints to retrieve today's day (with auto-creation), look up a
specific calendar date, and list all recorded days.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.day import Day
from app.schemas.daily_note import DailyNoteResponse, DailyNoteUpsert
from app.schemas.day import DayResponse
from app.schemas.day_metadata import DayMetadataResponse, DayMetadataUpsert
from app.schemas.day_off import DayOffResponse, DayOffUpsert
from app.schemas.day_rating import DayRatingResponse, DayRatingUpsert
from app.schemas.roadblock import RoadblockResponse, RoadblockUpsert
from app.services.day_service import DayService

router = APIRouter(prefix="/api/days", tags=["days"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_day_or_404(day_id: int, db: AsyncSession) -> Day:
    """Fetch a Day by primary key or raise a 404 HTTPException.

    Args:
        day_id: The primary key to look up.
        db: Open async session.

    Returns:
        The matching Day instance.

    Raises:
        HTTPException: 404 if no Day with ``day_id`` exists.
    """
    result = await db.execute(select(Day).where(Day.id == day_id))
    day = result.scalar_one_or_none()
    if day is None:
        raise HTTPException(status_code=404, detail=f"Day {day_id} not found")
    return day


# NOTE: Fixed-path routes (/off, /today, /next-working-day) must be registered
# BEFORE GET /api/days/{day_date} to prevent FastAPI from parsing them as dates.


@router.get("/next-working-day")
async def get_next_working_day(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Return the next working day after today, skipping weekends and days-off.

    Args:
        db: Injected async database session.

    Returns:
        A dict with key ``date`` formatted as ``YYYY-MM-DD``.
    """
    service = DayService(db)
    next_day = await service.get_next_working_day()
    return {"date": next_day.strftime("%Y-%m-%d")}


@router.get("/off", response_model=list[DayOffResponse])
async def list_days_off(db: AsyncSession = Depends(get_db)) -> list[DayOffResponse]:
    """Return all day-off records ordered by day_id descending.

    Args:
        db: Injected async database session.

    Returns:
        A list of DayOffResponse objects.
    """
    service = DayService(db)
    return await service.get_all_day_offs()


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
async def list_days(
    limit: int = Query(default=90, ge=1, le=365),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[DayResponse]:
    """Return Day records ordered newest-first with optional pagination.

    Args:
        limit: Maximum number of records to return (1–365, default 90).
        offset: Number of records to skip before returning results (default 0).
        db: Injected async database session.

    Returns:
        A list of DayResponse objects sorted by date descending.
    """
    service = DayService(db)
    return await service.get_all(limit=limit, offset=offset)


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
    await _get_day_or_404(day_id, db)
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
    await _get_day_or_404(day_id, db)
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
    await _get_day_or_404(day_id, db)
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
    await _get_day_or_404(day_id, db)
    service = DayService(db)
    meta = await service.upsert_metadata(
        day_id, payload.temperature_c, payload.condition, payload.moon_phase
    )
    await db.commit()
    return meta


@router.put("/{day_id}/day-off", response_model=DayOffResponse)
async def upsert_day_off(
    day_id: int,
    payload: DayOffUpsert,
    db: AsyncSession = Depends(get_db),
) -> DayOffResponse:
    """Create or update the day-off record for a day.

    Args:
        day_id: Primary key of the target Day.
        payload: Reason and optional note.
        db: Injected async database session.

    Returns:
        The saved DayOffResponse.
    """
    await _get_day_or_404(day_id, db)
    service = DayService(db)
    day_off = await service.upsert_day_off(day_id, payload.reason, payload.note)
    await db.commit()
    return day_off


@router.delete("/{day_id}/day-off", status_code=204, response_class=Response)
async def remove_day_off(
    day_id: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Remove the day-off record for a day (idempotent).

    Args:
        day_id: Primary key of the target Day.
        db: Injected async database session.
    """
    service = DayService(db)
    await service.remove_day_off(day_id)
    await db.commit()
    return Response(status_code=204)
