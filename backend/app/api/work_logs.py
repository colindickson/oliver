"""API routes for the WorkLog resource.

Provides endpoints to list work logs for a day and update tags on a work log.
All database access uses async SQLAlchemy so the routes remain non-blocking.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.day import Day
from app.schemas.work_log import WorkLogResponse, WorkLogTagsUpdate
from app.services.work_log_service import WorkLogService

# No prefix: endpoints span two URL hierarchies (/api/days/ and /api/work-logs/).
router = APIRouter(tags=["work_logs"])


@router.get("/api/days/{day_date}/work-logs", response_model=list[WorkLogResponse])
async def list_work_logs_for_day(
    day_date: date, db: AsyncSession = Depends(get_db)
) -> list[WorkLogResponse]:
    """Return all WorkLog entries for the given day date.

    If the day does not yet exist, returns an empty list rather than 404.

    Args:
        day_date: ISO date string parsed by FastAPI automatically.
        db: Injected async database session.

    Returns:
        Ordered list of WorkLogResponse objects (empty if day not found).
    """
    result = await db.execute(select(Day).where(Day.date == day_date))
    day = result.scalar_one_or_none()
    if day is None:
        return []

    work_logs = await WorkLogService(db).get_by_day_id(day.id)
    return work_logs


@router.patch("/api/work-logs/{work_log_id}/tags", response_model=WorkLogResponse)
async def update_work_log_tags(
    work_log_id: int,
    payload: WorkLogTagsUpdate,
    db: AsyncSession = Depends(get_db),
) -> WorkLogResponse:
    """Replace the tags on a WorkLog.

    Args:
        work_log_id: Primary key of the WorkLog to update.
        payload: Contains the new tag list.
        db: Injected async database session.

    Returns:
        The updated WorkLogResponse.

    Raises:
        HTTPException: 404 if no WorkLog with ``work_log_id`` exists.
        HTTPException: 400 if more than MAX_TAGS_PER_TASK tags are provided.
    """
    work_log = await WorkLogService(db).update_tags(work_log_id, payload.tags)
    await db.commit()
    return work_log
