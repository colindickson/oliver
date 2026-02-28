"""Integration tests for recurring schedule application on day open."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.main import app
from app.database import Base, get_db
from app.models import Day, Task  # noqa: F401 — register all tables
from app.models.task_template import TaskTemplate, TemplateSchedule  # noqa: F401
from app.models.day_off import DayOff  # noqa: F401

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session() -> AsyncSession:
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
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


async def _make_template_with_schedule(
    db: AsyncSession,
    recurrence: str,
    next_run_date: date,
    category: str = "short_task",
) -> TemplateSchedule:
    """Helper: insert a template + schedule directly into the DB."""
    template = TaskTemplate(title="Yoga", category=category)
    db.add(template)
    await db.flush()
    schedule = TemplateSchedule(
        template_id=template.id,
        recurrence=recurrence,
        anchor_date=next_run_date,
        next_run_date=next_run_date,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def test_schedule_due_today_creates_task(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Opening a day with a due schedule auto-creates the task."""
    today = date.today()
    schedule = await _make_template_with_schedule(db_session, "weekly", today)

    response = await client.get(f"/api/days/{today.isoformat()}")

    assert response.status_code == 200
    tasks = response.json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Yoga"

    # next_run_date should have advanced by 7 days
    await db_session.refresh(schedule)
    from datetime import timedelta
    assert schedule.next_run_date == today + timedelta(days=7)


async def test_schedule_due_today_on_day_off_skips_task(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Opening a day marked as day-off does NOT create the task but still advances cursor."""
    today = date.today()

    # First open today to create the Day row
    day_resp = await client.get(f"/api/days/{today.isoformat()}")
    day_id = day_resp.json()["id"]

    # Mark today as a day off
    await client.put(f"/api/days/{day_id}/day-off", json={"reason": "personal_day"})

    # Now create the schedule AFTER marking as day off (so it hasn't been applied yet)
    # Set next_run_date to today
    schedule = await _make_template_with_schedule(db_session, "weekly", today)

    # Open today again — schedule should be evaluated but task NOT created
    response = await client.get(f"/api/days/{today.isoformat()}")
    tasks = response.json()["tasks"]
    assert len(tasks) == 0  # no task because day is off

    # Cursor should still have advanced
    await db_session.refresh(schedule)
    from datetime import timedelta
    assert schedule.next_run_date == today + timedelta(days=7)


async def test_schedule_future_not_applied(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A schedule with next_run_date in the future is not applied."""
    from datetime import timedelta
    future = date.today() + timedelta(days=3)
    await _make_template_with_schedule(db_session, "weekly", future)

    response = await client.get(f"/api/days/{date.today().isoformat()}")
    assert response.json()["tasks"] == []


async def test_schedule_missed_advances_without_creating_task(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A schedule due 3 days ago advances past today without creating a task for today."""
    from datetime import timedelta
    past = date.today() - timedelta(days=3)
    today = date.today()
    schedule = await _make_template_with_schedule(db_session, "weekly", past)

    response = await client.get(f"/api/days/{today.isoformat()}")
    # past date ≠ today so no task is created for today
    assert response.json()["tasks"] == []

    await db_session.refresh(schedule)
    # next_run_date should now be beyond today
    assert schedule.next_run_date > today


async def test_schedule_idempotent(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Opening the same day twice does not double-create tasks."""
    today = date.today()
    await _make_template_with_schedule(db_session, "weekly", today)

    await client.get(f"/api/days/{today.isoformat()}")
    response = await client.get(f"/api/days/{today.isoformat()}")

    assert len(response.json()["tasks"]) == 1
