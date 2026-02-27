"""Tests for the days-off feature.

Covers:
- PUT /api/days/{id}/day-off (upsert)
- DELETE /api/days/{id}/day-off (remove)
- GET /api/days/off (list all)
- GET /api/days/{date} includes day_off field
- GET /api/settings/recurring-days-off
- PUT /api/settings/recurring-days-off
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.models import Day  # ensure all tables are registered


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


@pytest.fixture
async def day(db_session: AsyncSession) -> Day:
    """Create and return a test Day record."""
    d = Day(date=date(2025, 6, 15), created_at=datetime.now(timezone.utc))
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


# ---------------------------------------------------------------------------
# PUT /api/days/{day_id}/day-off
# ---------------------------------------------------------------------------


async def test_upsert_day_off_creates_record(
    client: AsyncClient, day: Day
) -> None:
    """PUT /{day_id}/day-off with valid reason creates record and returns correct fields."""
    response = await client.put(
        f"/api/days/{day.id}/day-off",
        json={"reason": "sick_day", "note": "stayed home with a cold"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["day_id"] == day.id
    assert payload["reason"] == "sick_day"
    assert payload["note"] == "stayed home with a cold"
    assert "id" in payload


async def test_upsert_day_off_without_note(
    client: AsyncClient, day: Day
) -> None:
    """PUT /{day_id}/day-off with no note stores null note."""
    response = await client.put(
        f"/api/days/{day.id}/day-off",
        json={"reason": "vacation"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reason"] == "vacation"
    assert payload["note"] is None


async def test_upsert_day_off_rejects_invalid_reason(
    client: AsyncClient, day: Day
) -> None:
    """PUT /{day_id}/day-off with invalid reason returns 422."""
    response = await client.put(
        f"/api/days/{day.id}/day-off",
        json={"reason": "laziness"},
    )

    assert response.status_code == 422


async def test_upsert_day_off_updates_when_called_twice(
    client: AsyncClient, day: Day, db_session: AsyncSession
) -> None:
    """PUT /{day_id}/day-off called twice updates the existing record."""
    await client.put(
        f"/api/days/{day.id}/day-off",
        json={"reason": "sick_day", "note": "first"},
    )

    response = await client.put(
        f"/api/days/{day.id}/day-off",
        json={"reason": "vacation", "note": "updated"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reason"] == "vacation"
    assert payload["note"] == "updated"


async def test_upsert_day_off_all_valid_reasons(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """All 5 valid reasons are accepted."""
    valid_reasons = ["weekend", "personal_day", "vacation", "holiday", "sick_day"]

    for i, reason in enumerate(valid_reasons):
        d = Day(date=date(2025, 7, i + 1), created_at=datetime.now(timezone.utc))
        db_session.add(d)
        await db_session.commit()
        await db_session.refresh(d)

        response = await client.put(
            f"/api/days/{d.id}/day-off",
            json={"reason": reason},
        )
        assert response.status_code == 200, f"Failed for reason: {reason}"


# ---------------------------------------------------------------------------
# DELETE /api/days/{day_id}/day-off
# ---------------------------------------------------------------------------


async def test_delete_day_off_returns_204(
    client: AsyncClient, day: Day
) -> None:
    """DELETE /{day_id}/day-off removes the record and returns 204."""
    await client.put(
        f"/api/days/{day.id}/day-off",
        json={"reason": "sick_day"},
    )

    response = await client.delete(f"/api/days/{day.id}/day-off")

    assert response.status_code == 204


async def test_delete_day_off_is_idempotent(
    client: AsyncClient, day: Day
) -> None:
    """DELETE /{day_id}/day-off returns 204 even when no record exists."""
    response = await client.delete(f"/api/days/{day.id}/day-off")

    assert response.status_code == 204


async def test_delete_day_off_clears_field_on_day(
    client: AsyncClient, day: Day, db_session: AsyncSession
) -> None:
    """After DELETE, GET /days/{date} returns day_off: null."""
    await client.put(
        f"/api/days/{day.id}/day-off",
        json={"reason": "sick_day"},
    )
    await client.delete(f"/api/days/{day.id}/day-off")

    # Expire session so relationship is re-loaded
    db_session.expire(day)

    response = await client.get(f"/api/days/2025-06-15")

    assert response.status_code == 200
    assert response.json()["day_off"] is None


# ---------------------------------------------------------------------------
# GET /api/days/off
# ---------------------------------------------------------------------------


async def test_list_days_off_returns_empty_when_none(
    client: AsyncClient,
) -> None:
    """GET /api/days/off returns empty list when no off days set."""
    response = await client.get("/api/days/off")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_days_off_returns_all_records(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /api/days/off returns all day-off records."""
    for i in range(3):
        d = Day(date=date(2025, 8, i + 1), created_at=datetime.now(timezone.utc))
        db_session.add(d)
        await db_session.commit()
        await db_session.refresh(d)
        await client.put(
            f"/api/days/{d.id}/day-off",
            json={"reason": "vacation"},
        )

    response = await client.get("/api/days/off")

    assert response.status_code == 200
    assert len(response.json()) == 3


# ---------------------------------------------------------------------------
# GET /api/days/{date} — day_off field in DayResponse
# ---------------------------------------------------------------------------


async def test_get_day_includes_day_off_when_set(
    client: AsyncClient, day: Day, db_session: AsyncSession
) -> None:
    """GET /days/{date} includes day_off field with data when set."""
    await client.put(
        f"/api/days/{day.id}/day-off",
        json={"reason": "holiday", "note": "Christmas"},
    )

    db_session.expire(day)

    response = await client.get("/api/days/2025-06-15")

    assert response.status_code == 200
    payload = response.json()
    assert payload["day_off"] is not None
    assert payload["day_off"]["reason"] == "holiday"
    assert payload["day_off"]["note"] == "Christmas"


async def test_get_day_returns_null_day_off_when_absent(
    client: AsyncClient, day: Day
) -> None:
    """GET /days/{date} returns day_off: null when no off day set."""
    response = await client.get("/api/days/2025-06-15")

    assert response.status_code == 200
    assert response.json()["day_off"] is None


# ---------------------------------------------------------------------------
# GET /api/settings/recurring-days-off
# ---------------------------------------------------------------------------


async def test_get_recurring_days_off_returns_empty_by_default(
    client: AsyncClient,
) -> None:
    """GET /api/settings/recurring-days-off returns empty list when nothing set."""
    response = await client.get("/api/settings/recurring-days-off")

    assert response.status_code == 200
    assert response.json() == {"days": []}


# ---------------------------------------------------------------------------
# PUT /api/settings/recurring-days-off
# ---------------------------------------------------------------------------


async def test_put_recurring_days_off_saves_valid_list(
    client: AsyncClient,
) -> None:
    """PUT /api/settings/recurring-days-off saves and returns valid weekday list."""
    response = await client.put(
        "/api/settings/recurring-days-off",
        json={"days": ["saturday", "sunday"]},
    )

    assert response.status_code == 200
    assert response.json() == {"days": ["saturday", "sunday"]}


async def test_put_recurring_days_off_rejects_invalid_weekday(
    client: AsyncClient,
) -> None:
    """PUT /api/settings/recurring-days-off returns 422 for invalid weekday name."""
    response = await client.put(
        "/api/settings/recurring-days-off",
        json={"days": ["saturday", "funday"]},
    )

    assert response.status_code == 422


async def test_put_recurring_days_off_accepts_empty_list(
    client: AsyncClient,
) -> None:
    """PUT /api/settings/recurring-days-off accepts empty list to clear all."""
    await client.put(
        "/api/settings/recurring-days-off",
        json={"days": ["saturday"]},
    )

    response = await client.put(
        "/api/settings/recurring-days-off",
        json={"days": []},
    )

    assert response.status_code == 200
    assert response.json() == {"days": []}


async def test_get_recurring_days_off_reflects_put(
    client: AsyncClient,
) -> None:
    """GET after PUT returns the stored weekdays."""
    await client.put(
        "/api/settings/recurring-days-off",
        json={"days": ["monday", "friday"]},
    )

    response = await client.get("/api/settings/recurring-days-off")

    assert response.status_code == 200
    assert set(response.json()["days"]) == {"monday", "friday"}
