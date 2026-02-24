"""Analytics API router — exposes summary, streaks, and category-time endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.analytics import (
    CategoriesResponse,
    StreaksResponse,
    SummaryResponse,
    TodayDeepWorkResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    """Return aggregated task-completion statistics for a rolling time window.

    Args:
        days: Number of calendar days to look back (1–365).  Defaults to 30.
        db: Injected database session.

    Returns:
        A ``SummaryResponse`` with period metrics.
    """
    data = await AnalyticsService(db).get_summary(days)
    return SummaryResponse(**data)


@router.get("/streaks", response_model=StreaksResponse)
async def get_streaks(db: AsyncSession = Depends(get_db)) -> StreaksResponse:
    """Return the current and all-time longest completion streaks.

    Args:
        db: Injected database session.

    Returns:
        A ``StreaksResponse`` with ``current_streak`` and ``longest_streak``.
    """
    data = await AnalyticsService(db).get_streaks()
    return StreaksResponse(**data)


@router.get("/categories", response_model=CategoriesResponse)
async def get_categories(db: AsyncSession = Depends(get_db)) -> CategoriesResponse:
    """Return total time spent and task count per category across all history.

    Args:
        db: Injected database session.

    Returns:
        A ``CategoriesResponse`` containing one entry per category with
        recorded timer sessions.
    """
    data = await AnalyticsService(db).get_category_time()
    return CategoriesResponse(**data)


@router.get("/today-deep-work", response_model=TodayDeepWorkResponse)
async def get_today_deep_work(
    db: AsyncSession = Depends(get_db),
) -> TodayDeepWorkResponse:
    """Return today's total deep work time and the 3-hour goal.

    Args:
        db: Injected database session.

    Returns:
        A ``TodayDeepWorkResponse`` with ``total_seconds`` and ``goal_seconds``.
    """
    data = await AnalyticsService(db).get_today_deep_work_time()
    return TodayDeepWorkResponse(**data)
