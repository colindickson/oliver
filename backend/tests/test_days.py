"""Tests for the /api/days endpoints.

Written before the implementation exists (TDD red phase).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.models import Day, Task  # ensure all tables are registered


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
# GET /api/days/today
# ---------------------------------------------------------------------------


async def test_get_today_auto_creates_day(client: AsyncClient) -> None:
    """GET /api/days/today should create today's Day record when none exists."""
    response = await client.get("/api/days/today")

    assert response.status_code == 200
    payload = response.json()
    assert payload["date"] == date.today().isoformat()
    assert "id" in payload
    assert "created_at" in payload
    assert isinstance(payload["tasks"], list)


async def test_get_today_is_idempotent(client: AsyncClient) -> None:
    """Calling GET /api/days/today twice must return the same Day id."""
    r1 = await client.get("/api/days/today")
    r2 = await client.get("/api/days/today")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]


async def test_get_today_returns_tasks_list(client: AsyncClient) -> None:
    """GET /api/days/today response includes a ``tasks`` array."""
    response = await client.get("/api/days/today")

    assert response.status_code == 200
    assert "tasks" in response.json()
    assert response.json()["tasks"] == []


# ---------------------------------------------------------------------------
# GET /api/days/{date}
# ---------------------------------------------------------------------------


async def test_get_day_by_date_returns_existing_day(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /api/days/{date} returns the correct day for a valid date string."""
    target = date(2025, 6, 15)
    day = Day(date=target, created_at=datetime.now(timezone.utc))
    db_session.add(day)
    await db_session.commit()
    await db_session.refresh(day)

    response = await client.get(f"/api/days/{target.isoformat()}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["date"] == target.isoformat()
    assert payload["id"] == day.id


async def test_get_day_by_date_returns_404_when_missing(client: AsyncClient) -> None:
    """GET /api/days/{date} returns 404 when no record exists for that date."""
    response = await client.get("/api/days/1999-01-01")

    assert response.status_code == 404
    assert response.json()["detail"] == "Day not found"


# ---------------------------------------------------------------------------
# GET /api/days
# ---------------------------------------------------------------------------


async def test_list_days_returns_empty_list(client: AsyncClient) -> None:
    """GET /api/days returns an empty list when there are no days."""
    response = await client.get("/api/days")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_days_returns_all_days_ordered_desc(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /api/days returns all days ordered newest-first."""
    dates = [date(2025, 1, 1), date(2025, 3, 1), date(2025, 2, 1)]
    for d in dates:
        db_session.add(Day(date=d, created_at=datetime.now(timezone.utc)))
    await db_session.commit()

    response = await client.get("/api/days")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 3
    returned_dates = [item["date"] for item in payload]
    assert returned_dates == ["2025-03-01", "2025-02-01", "2025-01-01"]
