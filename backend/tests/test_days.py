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


async def test_get_day_by_date_auto_creates_when_missing(client: AsyncClient) -> None:
    """GET /api/days/{date} creates and returns the Day when none exists."""
    response = await client.get("/api/days/2030-06-15")

    assert response.status_code == 200
    payload = response.json()
    assert payload["date"] == "2030-06-15"
    assert "id" in payload
    assert isinstance(payload["tasks"], list)


async def test_get_day_by_date_auto_create_is_idempotent(client: AsyncClient) -> None:
    """GET /api/days/{date} called twice returns the same Day id."""
    r1 = await client.get("/api/days/2030-06-15")
    r2 = await client.get("/api/days/2030-06-15")

    assert r1.json()["id"] == r2.json()["id"]


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


# ---------------------------------------------------------------------------
# PUT /api/days/{day_id}/metadata
# ---------------------------------------------------------------------------


async def test_upsert_metadata_creates_when_absent(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """PUT /{day_id}/metadata creates a new record and returns correct fields."""
    day = Day(date=date(2025, 6, 15), created_at=datetime.now(timezone.utc))
    db_session.add(day)
    await db_session.commit()
    await db_session.refresh(day)

    response = await client.put(
        f"/api/days/{day.id}/metadata",
        json={"temperature_c": 22.5, "condition": "sunny", "moon_phase": "full_moon"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["day_id"] == day.id
    assert payload["temperature_c"] == 22.5
    assert payload["condition"] == "sunny"
    assert payload["moon_phase"] == "full_moon"
    assert "id" in payload


async def test_upsert_metadata_updates_when_present(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """PUT /{day_id}/metadata overwrites existing record."""
    day = Day(date=date(2025, 6, 16), created_at=datetime.now(timezone.utc))
    db_session.add(day)
    await db_session.commit()
    await db_session.refresh(day)

    await client.put(
        f"/api/days/{day.id}/metadata",
        json={"temperature_c": 10.0, "condition": "cloudy", "moon_phase": "new_moon"},
    )
    response = await client.put(
        f"/api/days/{day.id}/metadata",
        json={"temperature_c": 18.0, "condition": "rainy", "moon_phase": "waxing_crescent"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["temperature_c"] == 18.0
    assert payload["condition"] == "rainy"
    assert payload["moon_phase"] == "waxing_crescent"


async def test_get_day_includes_metadata_when_set(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /days/{date} includes day_metadata field when metadata has been set."""
    day = Day(date=date(2025, 7, 1), created_at=datetime.now(timezone.utc))
    db_session.add(day)
    await db_session.commit()
    await db_session.refresh(day)

    await client.put(
        f"/api/days/{day.id}/metadata",
        json={"temperature_c": 25.0, "condition": "partly_cloudy", "moon_phase": "waxing_gibbous"},
    )

    # Expire cached Day so the next query re-loads relationships (including day_metadata)
    # from the database rather than returning the identity-map entry with day_metadata=None.
    db_session.expire(day)

    response = await client.get("/api/days/2025-07-01")

    assert response.status_code == 200
    payload = response.json()
    assert payload["day_metadata"] is not None
    assert payload["day_metadata"]["condition"] == "partly_cloudy"
    assert payload["day_metadata"]["moon_phase"] == "waxing_gibbous"
    assert payload["day_metadata"]["temperature_c"] == 25.0


async def test_get_day_returns_null_metadata_when_absent(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /days/{date} returns day_metadata: null when no metadata has been set."""
    day = Day(date=date(2025, 8, 1), created_at=datetime.now(timezone.utc))
    db_session.add(day)
    await db_session.commit()

    response = await client.get("/api/days/2025-08-01")

    assert response.status_code == 200
    assert response.json()["day_metadata"] is None


async def test_upsert_metadata_rejects_invalid_condition(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """PUT /{day_id}/metadata returns 422 for an invalid condition value."""
    day = Day(date=date(2025, 9, 1), created_at=datetime.now(timezone.utc))
    db_session.add(day)
    await db_session.commit()
    await db_session.refresh(day)

    response = await client.put(
        f"/api/days/{day.id}/metadata",
        json={"condition": "hailstorm"},
    )

    assert response.status_code == 422
