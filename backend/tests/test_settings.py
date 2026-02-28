"""Tests for the settings API endpoints.

Covers:
- GET /api/settings/timer-display (default true)
- PUT /api/settings/timer-display (save false)
- PUT /api/settings/timer-display (save true)
- GET after PUT reflects stored value
"""

from __future__ import annotations

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


async def test_get_timer_display_default(client: AsyncClient) -> None:
    """GET timer-display returns enabled=true when no setting has been stored."""
    response = await client.get("/api/settings/timer-display")
    assert response.status_code == 200
    assert response.json() == {"enabled": True}


async def test_put_timer_display_false(client: AsyncClient) -> None:
    """PUT timer-display with enabled=false saves and returns false."""
    response = await client.put("/api/settings/timer-display", json={"enabled": False})
    assert response.status_code == 200
    assert response.json() == {"enabled": False}


async def test_put_timer_display_true(client: AsyncClient) -> None:
    """PUT timer-display with enabled=true saves and returns true."""
    response = await client.put("/api/settings/timer-display", json={"enabled": True})
    assert response.status_code == 200
    assert response.json() == {"enabled": True}


async def test_get_timer_display_reflects_stored_value(client: AsyncClient) -> None:
    """GET timer-display after PUT returns the last stored value."""
    await client.put("/api/settings/timer-display", json={"enabled": False})
    response = await client.get("/api/settings/timer-display")
    assert response.status_code == 200
    assert response.json() == {"enabled": False}

    await client.put("/api/settings/timer-display", json={"enabled": True})
    response = await client.get("/api/settings/timer-display")
    assert response.status_code == 200
    assert response.json() == {"enabled": True}
