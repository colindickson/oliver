"""Tests for the /api/analytics endpoints.

Written before the implementation exists (TDD red phase).
Covers summary, streaks, and category-time breakdown endpoints.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.models import Day, Task, TimerSession  # ensure all tables are registered


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session() -> AsyncSession:
    """Provide an isolated in-memory SQLite session per test."""
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """Provide an AsyncClient wired to the in-memory test database."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_day_with_tasks(
    session: AsyncSession,
    target_date: date,
    *,
    categories: list[str] | None = None,
    completed_count: int = 0,
) -> Day:
    """Insert a Day and associated Task rows into the database.

    Args:
        session: The active async session.
        target_date: Calendar date for the new Day.
        categories: List of category strings for the tasks; defaults to three
            ``deep_work`` tasks.
        completed_count: How many tasks (from index 0) to mark as completed.

    Returns:
        The persisted Day instance.
    """
    if categories is None:
        categories = ["deep_work", "short_task", "maintenance"]

    day = Day(date=target_date, created_at=datetime.now(timezone.utc))
    session.add(day)
    await session.commit()
    await session.refresh(day)

    for i, cat in enumerate(categories):
        status = "completed" if i < completed_count else "pending"
        completed_at = datetime.now(timezone.utc) if status == "completed" else None
        task = Task(
            day_id=day.id,
            category=cat,
            title=f"Task {i}",
            status=status,
            order_index=i,
            completed_at=completed_at,
        )
        session.add(task)

    await session.commit()
    await session.refresh(day)
    return day


# ---------------------------------------------------------------------------
# GET /api/analytics/summary
# ---------------------------------------------------------------------------


async def test_summary_returns_expected_fields(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /api/analytics/summary returns all required fields with correct types."""
    today = date.today()
    await _seed_day_with_tasks(
        db_session,
        today,
        categories=["deep_work", "short_task", "maintenance"],
        completed_count=2,
    )

    response = await client.get("/api/analytics/summary")

    assert response.status_code == 200
    payload = response.json()
    assert "period_days" in payload
    assert "total_days_tracked" in payload
    assert "total_tasks" in payload
    assert "completed_tasks" in payload
    assert "completion_rate_pct" in payload


async def test_summary_counts_are_correct(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /api/analytics/summary aggregates tasks accurately."""
    today = date.today()
    # Day 1: 3 tasks, 2 completed (excluded from tracking - today is in progress)
    await _seed_day_with_tasks(
        db_session,
        today,
        categories=["deep_work", "short_task", "maintenance"],
        completed_count=2,
    )
    # Day 2: 3 tasks, 1 completed  (within default 30-day window)
    yesterday = today - timedelta(days=1)
    await _seed_day_with_tasks(
        db_session,
        yesterday,
        categories=["deep_work", "short_task", "maintenance"],
        completed_count=1,
    )

    response = await client.get("/api/analytics/summary")

    assert response.status_code == 200
    payload = response.json()
    # Today is excluded (in progress), so only yesterday counts
    assert payload["total_days_tracked"] == 1
    assert payload["total_tasks"] == 3
    assert payload["completed_tasks"] == 1
    assert payload["completion_rate_pct"] == 33.33
    assert payload["period_days"] == 30


async def test_summary_respects_days_query_param(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /api/analytics/summary?days=7 excludes days older than 7 days."""
    today = date.today()
    # Within window (yesterday - will be counted)
    yesterday = today - timedelta(days=1)
    await _seed_day_with_tasks(
        db_session,
        yesterday,
        categories=["deep_work"],
        completed_count=1,
    )
    # Outside the 7-day window
    old_date = today - timedelta(days=10)
    await _seed_day_with_tasks(
        db_session,
        old_date,
        categories=["deep_work", "short_task"],
        completed_count=2,
    )

    response = await client.get("/api/analytics/summary?days=7")

    assert response.status_code == 200
    payload = response.json()
    assert payload["period_days"] == 7
    assert payload["total_days_tracked"] == 1  # only yesterday
    assert payload["total_tasks"] == 1
    assert payload["completed_tasks"] == 1


async def test_summary_excludes_empty_days(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Days with no tasks AND no notes are not counted as tracked days."""
    today = date.today()
    # Day with tasks - should be counted
    yesterday = today - timedelta(days=1)
    await _seed_day_with_tasks(
        db_session,
        yesterday,
        categories=["deep_work"],
        completed_count=1,
    )
    # Empty day (no tasks, no notes) - should NOT be counted
    two_days_ago = today - timedelta(days=2)
    empty_day = Day(date=two_days_ago, created_at=datetime.now(timezone.utc))
    db_session.add(empty_day)

    await db_session.commit()

    response = await client.get("/api/analytics/summary")

    assert response.status_code == 200
    payload = response.json()
    # Only yesterday counts (two_days_ago is empty, today is excluded)
    assert payload["total_days_tracked"] == 1


# ---------------------------------------------------------------------------
# GET /api/analytics/streaks
# ---------------------------------------------------------------------------


async def test_streaks_with_no_data(client: AsyncClient) -> None:
    """GET /api/analytics/streaks with no days returns zeros."""
    response = await client.get("/api/analytics/streaks")

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_streak"] == 0
    assert payload["longest_streak"] == 0


async def test_streaks_counts_consecutive_complete_days(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /api/analytics/streaks returns correct current and longest streak.

    Setup: seed the last 3 consecutive workdays all fully completed.
    Weekends are skipped, so we walk back to find 3 actual weekdays.
    Today is excluded (in progress), so streak counts from yesterday backwards.
    current_streak and longest_streak should be 2 (yesterday and day before).
    """
    workdays: list[date] = []
    cursor = date.today()
    while len(workdays) < 3:
        if cursor.weekday() < 5:  # Monday=0 … Friday=4
            workdays.append(cursor)
        cursor -= timedelta(days=1)

    for target in workdays:
        await _seed_day_with_tasks(
            db_session,
            target,
            categories=["deep_work", "short_task"],
            completed_count=2,  # all tasks done
        )

    response = await client.get("/api/analytics/streaks")

    assert response.status_code == 200
    payload = response.json()
    # Today is excluded, so only yesterday and day before count
    assert payload["current_streak"] == 2
    assert payload["longest_streak"] == 2


async def test_streaks_breaks_on_incomplete_day(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A day with incomplete tasks breaks the current streak."""
    today = date.today()
    # Today: all complete -> excluded (in progress)
    await _seed_day_with_tasks(
        db_session,
        today,
        categories=["deep_work"],
        completed_count=1,
    )
    # Yesterday: incomplete -> breaks streak
    yesterday = today - timedelta(days=1)
    await _seed_day_with_tasks(
        db_session,
        yesterday,
        categories=["deep_work", "short_task"],
        completed_count=0,  # nothing done
    )
    # Two days ago: all complete
    two_days_ago = today - timedelta(days=2)
    await _seed_day_with_tasks(
        db_session,
        two_days_ago,
        categories=["deep_work"],
        completed_count=1,
    )

    response = await client.get("/api/analytics/streaks")

    assert response.status_code == 200
    payload = response.json()
    # current streak is 0 (yesterday broke it, today excluded)
    assert payload["current_streak"] == 0
    # longest streak is 1 (two_days_ago)
    assert payload["longest_streak"] == 1


# ---------------------------------------------------------------------------
# GET /api/analytics/categories
# ---------------------------------------------------------------------------


async def test_categories_returns_time_per_category(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /api/analytics/categories sums duration_seconds by category."""
    today = date.today()
    day = await _seed_day_with_tasks(
        db_session,
        today,
        categories=["deep_work", "short_task"],
        completed_count=2,
    )
    tasks = day.tasks

    # Add timer sessions: 120s for deep_work, 60s for short_task
    deep_task = next(t for t in tasks if t.category == "deep_work")
    short_task = next(t for t in tasks if t.category == "short_task")

    now = datetime.now(timezone.utc)
    db_session.add(
        TimerSession(
            task_id=deep_task.id,
            started_at=now - timedelta(seconds=120),
            ended_at=now,
            duration_seconds=120,
        )
    )
    db_session.add(
        TimerSession(
            task_id=short_task.id,
            started_at=now - timedelta(seconds=60),
            ended_at=now,
            duration_seconds=60,
        )
    )
    await db_session.commit()

    response = await client.get("/api/analytics/categories")

    assert response.status_code == 200
    payload = response.json()
    assert "entries" in payload

    by_category = {e["category"]: e for e in payload["entries"]}
    assert "deep_work" in by_category
    assert "short_task" in by_category
    assert by_category["deep_work"]["total_seconds"] == 120
    assert by_category["short_task"]["total_seconds"] == 60
    assert by_category["deep_work"]["task_count"] == 1
    assert by_category["short_task"]["task_count"] == 1


async def test_categories_empty_when_no_sessions(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /api/analytics/categories returns an empty entries list when no timer sessions exist."""
    response = await client.get("/api/analytics/categories")

    assert response.status_code == 200
    payload = response.json()
    assert payload["entries"] == []


# ---------------------------------------------------------------------------
# GET /api/analytics/today-deep-work
# ---------------------------------------------------------------------------


async def test_today_deep_work_returns_expected_fields(client: AsyncClient) -> None:
    """GET /api/analytics/today-deep-work returns required fields."""
    response = await client.get("/api/analytics/today-deep-work")

    assert response.status_code == 200
    payload = response.json()
    assert "total_seconds" in payload
    assert "goal_seconds" in payload
    assert payload["goal_seconds"] == 10800  # 3 hours


async def test_today_deep_work_sums_sessions(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /api/analytics/today-deep-work sums all deep work timer sessions for today."""
    today = date.today()
    day = await _seed_day_with_tasks(
        db_session,
        today,
        categories=["deep_work", "deep_work", "short_task"],
        completed_count=3,
    )
    tasks = day.tasks

    deep_tasks = [t for t in tasks if t.category == "deep_work"]
    short_task = next(t for t in tasks if t.category == "short_task")

    now = datetime.now(timezone.utc)
    # Add timer sessions: two deep work sessions of 1800s each
    for task in deep_tasks:
        db_session.add(
            TimerSession(
                task_id=task.id,
                started_at=now - timedelta(seconds=1800),
                ended_at=now,
                duration_seconds=1800,
            )
        )
    # Add a short_task session (should be excluded)
    db_session.add(
        TimerSession(
            task_id=short_task.id,
            started_at=now - timedelta(seconds=600),
            ended_at=now,
            duration_seconds=600,
        )
    )
    await db_session.commit()

    response = await client.get("/api/analytics/today-deep-work")

    assert response.status_code == 200
    payload = response.json()
    # Should sum only deep work sessions: 1800 + 1800 = 3600
    assert payload["total_seconds"] == 3600
    assert payload["goal_seconds"] == 10800


async def test_today_deep_work_excludes_other_days(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /api/analytics/today-deep-work only counts sessions from today."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    # Today's day with deep work task
    today_day = await _seed_day_with_tasks(
        db_session,
        today,
        categories=["deep_work"],
        completed_count=1,
    )
    today_task = today_day.tasks[0]

    # Yesterday's day with deep work task
    yesterday_day = await _seed_day_with_tasks(
        db_session,
        yesterday,
        categories=["deep_work"],
        completed_count=1,
    )
    yesterday_task = yesterday_day.tasks[0]

    now = datetime.now(timezone.utc)
    # Add session for today
    db_session.add(
        TimerSession(
            task_id=today_task.id,
            started_at=now - timedelta(seconds=900),
            ended_at=now,
            duration_seconds=900,
        )
    )
    # Add session for yesterday
    db_session.add(
        TimerSession(
            task_id=yesterday_task.id,
            started_at=now - timedelta(seconds=1200),
            ended_at=now,
            duration_seconds=1200,
        )
    )
    await db_session.commit()

    response = await client.get("/api/analytics/today-deep-work")

    assert response.status_code == 200
    payload = response.json()
    # Should only count today's session
    assert payload["total_seconds"] == 900


async def test_today_deep_work_returns_zero_when_no_sessions(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /api/analytics/today-deep-work returns 0 when no timer sessions exist."""
    today = date.today()
    await _seed_day_with_tasks(
        db_session,
        today,
        categories=["deep_work"],
        completed_count=0,
    )

    response = await client.get("/api/analytics/today-deep-work")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_seconds"] == 0
    assert payload["goal_seconds"] == 10800
