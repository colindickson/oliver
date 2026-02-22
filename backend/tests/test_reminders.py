"""Tests for the /api/reminders endpoints.

Written before the implementation exists (TDD red phase).
"""

from __future__ import annotations

from datetime import date, datetime, timezone, timedelta

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.models import Day, Task, Reminder  # ensure all tables are registered
from app.models.task import CATEGORY_DEEP_WORK, STATUS_PENDING


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
    """Insert a Day record and return it for use in task tests."""
    d = Day(date=date(2025, 6, 1), created_at=datetime.now(timezone.utc))
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


@pytest.fixture
async def task(db_session: AsyncSession, day: Day) -> Task:
    """Insert a Task record under the day fixture and return it."""
    t = Task(
        day_id=day.id,
        category=CATEGORY_DEEP_WORK,
        title="Test task for reminders",
        status=STATUS_PENDING,
        order_index=0,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


# ---------------------------------------------------------------------------
# POST /api/reminders
# ---------------------------------------------------------------------------


async def test_create_reminder(client: AsyncClient, task: Task) -> None:
    """POST /api/reminders creates a reminder and returns ReminderResponse."""
    remind_at = datetime(2025, 6, 1, 9, 0, 0)
    payload = {
        "task_id": task.id,
        "remind_at": remind_at.isoformat(),
        "message": "Time to start your deep work session",
    }
    response = await client.post("/api/reminders", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["task_id"] == task.id
    assert body["message"] == "Time to start your deep work session"
    assert body["is_delivered"] is False
    assert "id" in body
    assert "remind_at" in body


# ---------------------------------------------------------------------------
# GET /api/reminders?task_id=X
# ---------------------------------------------------------------------------


async def test_list_reminders_for_task(client: AsyncClient, task: Task) -> None:
    """GET /api/reminders?task_id=X returns all reminders for that task."""
    for i, msg in enumerate(("First reminder", "Second reminder")):
        await client.post(
            "/api/reminders",
            json={
                "task_id": task.id,
                "remind_at": datetime(2025, 6, 1, 9 + i, 0, 0).isoformat(),
                "message": msg,
            },
        )

    response = await client.get(f"/api/reminders?task_id={task.id}")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    messages = {r["message"] for r in body}
    assert messages == {"First reminder", "Second reminder"}


# ---------------------------------------------------------------------------
# GET /api/reminders/due
# ---------------------------------------------------------------------------


async def test_get_due_reminders(client: AsyncClient, task: Task) -> None:
    """GET /api/reminders/due returns undelivered reminders where remind_at <= now."""
    past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).replace(tzinfo=None)
    future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None)

    # Past reminder — should appear in /due
    await client.post(
        "/api/reminders",
        json={
            "task_id": task.id,
            "remind_at": past_time.isoformat(),
            "message": "Overdue reminder",
        },
    )
    # Future reminder — should NOT appear in /due
    await client.post(
        "/api/reminders",
        json={
            "task_id": task.id,
            "remind_at": future_time.isoformat(),
            "message": "Future reminder",
        },
    )

    response = await client.get("/api/reminders/due")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["message"] == "Overdue reminder"


# ---------------------------------------------------------------------------
# PATCH /api/reminders/{id}/delivered
# ---------------------------------------------------------------------------


async def test_mark_reminder_delivered(client: AsyncClient, task: Task) -> None:
    """PATCH /api/reminders/{id}/delivered sets is_delivered to True."""
    create_resp = await client.post(
        "/api/reminders",
        json={
            "task_id": task.id,
            "remind_at": datetime(2025, 6, 1, 9, 0, 0).isoformat(),
            "message": "Deliver me",
        },
    )
    reminder_id = create_resp.json()["id"]

    patch_resp = await client.patch(f"/api/reminders/{reminder_id}/delivered")

    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["id"] == reminder_id
    assert body["is_delivered"] is True


# ---------------------------------------------------------------------------
# DELETE /api/reminders/{id}
# ---------------------------------------------------------------------------


async def test_delete_reminder(client: AsyncClient, task: Task) -> None:
    """DELETE /api/reminders/{id} removes the reminder and returns {"deleted": true}."""
    create_resp = await client.post(
        "/api/reminders",
        json={
            "task_id": task.id,
            "remind_at": datetime(2025, 6, 1, 9, 0, 0).isoformat(),
            "message": "Delete me",
        },
    )
    reminder_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/reminders/{reminder_id}")

    assert delete_resp.status_code == 200
    assert delete_resp.json() == {"deleted": True}


# ---------------------------------------------------------------------------
# GET /api/reminders/due — delivered reminders are excluded
# ---------------------------------------------------------------------------


async def test_due_reminders_excludes_delivered(client: AsyncClient, task: Task) -> None:
    """A reminder marked as delivered does NOT appear in GET /api/reminders/due."""
    past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).replace(tzinfo=None)

    create_resp = await client.post(
        "/api/reminders",
        json={
            "task_id": task.id,
            "remind_at": past_time.isoformat(),
            "message": "Already delivered",
        },
    )
    reminder_id = create_resp.json()["id"]

    # Mark it delivered
    await client.patch(f"/api/reminders/{reminder_id}/delivered")

    # /due must now be empty
    due_resp = await client.get("/api/reminders/due")

    assert due_resp.status_code == 200
    assert due_resp.json() == []
