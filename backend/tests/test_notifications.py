"""Tests for the /api/notifications endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.models import Notification  # ensure table is registered


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
# POST /api/notifications
# ---------------------------------------------------------------------------


async def test_create_notification(client: AsyncClient) -> None:
    """POST /api/notifications creates a notification and returns NotificationResponse."""
    payload = {
        "source": "timer",
        "content": "Your deep work session has ended.",
    }
    response = await client.post("/api/notifications", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "timer"
    assert body["content"] == "Your deep work session has ended."
    assert body["is_read"] is False
    assert "id" in body
    assert "created_at" in body


async def test_create_notification_content_too_long(client: AsyncClient) -> None:
    """POST /api/notifications rejects content exceeding 500 characters."""
    payload = {
        "source": "system",
        "content": "x" * 501,
    }
    response = await client.post("/api/notifications", json=payload)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/notifications
# ---------------------------------------------------------------------------


async def test_list_recent_default_limit(client: AsyncClient) -> None:
    """GET /api/notifications returns at most 5 notifications by default."""
    for i in range(7):
        await client.post(
            "/api/notifications",
            json={"source": "system", "content": f"Notification {i}"},
        )

    response = await client.get("/api/notifications")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 5


async def test_list_recent_custom_limit(client: AsyncClient) -> None:
    """GET /api/notifications?limit=N returns at most N notifications."""
    for i in range(4):
        await client.post(
            "/api/notifications",
            json={"source": "system", "content": f"Notification {i}"},
        )

    response = await client.get("/api/notifications?limit=3")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3


async def test_list_recent_ordered_newest_first(client: AsyncClient) -> None:
    """GET /api/notifications returns notifications ordered by created_at descending."""
    for i in range(3):
        await client.post(
            "/api/notifications",
            json={"source": "system", "content": f"Notification {i}"},
        )

    response = await client.get("/api/notifications?limit=3")

    assert response.status_code == 200
    body = response.json()
    # Most recently created has the highest ID (autoincrement)
    assert body[0]["id"] > body[1]["id"] > body[2]["id"]


# ---------------------------------------------------------------------------
# GET /api/notifications/unread
# ---------------------------------------------------------------------------


async def test_list_unread_returns_only_unread(client: AsyncClient) -> None:
    """GET /api/notifications/unread returns only notifications where is_read is False."""
    # Create two notifications
    r1 = await client.post(
        "/api/notifications",
        json={"source": "system", "content": "First notification"},
    )
    r2 = await client.post(
        "/api/notifications",
        json={"source": "system", "content": "Second notification"},
    )
    n1_id = r1.json()["id"]

    # Mark the first one as read
    await client.patch(f"/api/notifications/{n1_id}/read")

    response = await client.get("/api/notifications/unread")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == r2.json()["id"]
    assert body[0]["is_read"] is False


async def test_list_unread_empty_when_all_read(client: AsyncClient) -> None:
    """GET /api/notifications/unread returns empty list when all are read."""
    r = await client.post(
        "/api/notifications",
        json={"source": "system", "content": "Read me"},
    )
    n_id = r.json()["id"]
    await client.patch(f"/api/notifications/{n_id}/read")

    response = await client.get("/api/notifications/unread")

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# PATCH /api/notifications/{id}/read
# ---------------------------------------------------------------------------


async def test_mark_notification_read(client: AsyncClient) -> None:
    """PATCH /api/notifications/{id}/read sets is_read to True."""
    create_resp = await client.post(
        "/api/notifications",
        json={"source": "timer", "content": "Session complete"},
    )
    notification_id = create_resp.json()["id"]

    patch_resp = await client.patch(f"/api/notifications/{notification_id}/read")

    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["id"] == notification_id
    assert body["is_read"] is True


async def test_mark_notification_read_not_found(client: AsyncClient) -> None:
    """PATCH /api/notifications/{id}/read returns 404 for a missing notification."""
    response = await client.patch("/api/notifications/99999/read")

    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"
