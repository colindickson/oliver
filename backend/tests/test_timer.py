"""Tests for the /api/timer endpoints.

Written before the implementation exists (TDD red phase).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

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


@pytest.fixture
async def task(db_session: AsyncSession) -> Task:
    """Insert a Day and Task record and return the Task for use in timer tests."""
    day = Day(date=date(2025, 6, 1), created_at=datetime.now(timezone.utc))
    db_session.add(day)
    await db_session.commit()
    await db_session.refresh(day)

    t = Task(
        day_id=day.id,
        category="deep_work",
        title="Focus block",
        order_index=0,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


# ---------------------------------------------------------------------------
# POST /api/timer/start
# ---------------------------------------------------------------------------


async def test_start_timer(client: AsyncClient, task: Task) -> None:
    """POST /api/timer/start with {task_id} returns 200 and running state."""
    response = await client.post("/api/timer/start", json={"task_id": task.id})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert body["task_id"] == task.id
    assert body["elapsed_seconds"] >= 0


async def test_start_timer_twice_returns_409(client: AsyncClient, task: Task) -> None:
    """Starting a timer while one is already running returns 409 Conflict."""
    await client.post("/api/timer/start", json={"task_id": task.id})

    response = await client.post("/api/timer/start", json={"task_id": task.id})

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# GET /api/timer/current
# ---------------------------------------------------------------------------


async def test_get_current_timer_running(client: AsyncClient, task: Task) -> None:
    """GET /api/timer/current while running returns status=running and elapsed_seconds >= 0."""
    await client.post("/api/timer/start", json={"task_id": task.id})

    response = await client.get("/api/timer/current")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert body["task_id"] == task.id
    assert body["elapsed_seconds"] >= 0


async def test_get_current_timer_idle(client: AsyncClient) -> None:
    """GET /api/timer/current when no timer is active returns status=idle."""
    response = await client.get("/api/timer/current")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "idle"
    assert body["task_id"] is None
    assert body["elapsed_seconds"] == 0


# ---------------------------------------------------------------------------
# POST /api/timer/pause
# ---------------------------------------------------------------------------


async def test_pause_timer(client: AsyncClient, task: Task) -> None:
    """POST /api/timer/pause while running returns 200 and status=paused."""
    await client.post("/api/timer/start", json={"task_id": task.id})

    response = await client.post("/api/timer/pause")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "paused"
    assert body["task_id"] == task.id


async def test_pause_timer_when_not_running(client: AsyncClient) -> None:
    """POST /api/timer/pause when no timer is running returns 409."""
    response = await client.post("/api/timer/pause")

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# POST /api/timer/start (resume after pause)
# ---------------------------------------------------------------------------


async def test_resume_timer(client: AsyncClient, task: Task) -> None:
    """POST /api/timer/start after pause resumes with accumulated_seconds > 0."""
    await client.post("/api/timer/start", json={"task_id": task.id})
    await client.post("/api/timer/pause")

    response = await client.post("/api/timer/start", json={"task_id": task.id})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert body["task_id"] == task.id
    # accumulated_seconds is the time recorded before the resume
    assert body["accumulated_seconds"] >= 0


# ---------------------------------------------------------------------------
# POST /api/timer/stop
# ---------------------------------------------------------------------------


async def test_stop_timer_creates_session(
    client: AsyncClient, task: Task, db_session: AsyncSession
) -> None:
    """POST /api/timer/stop while running returns 200 and creates a TimerSession."""
    from sqlalchemy import select

    await client.post("/api/timer/start", json={"task_id": task.id})

    response = await client.post("/api/timer/stop")

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == task.id
    assert body["duration_seconds"] >= 0
    assert "id" in body

    # Confirm the session was persisted
    result = await db_session.execute(
        select(TimerSession).where(TimerSession.task_id == task.id)
    )
    sessions = list(result.scalars().all())
    assert len(sessions) == 1
    assert sessions[0].duration_seconds >= 0


async def test_stop_timer_when_idle(client: AsyncClient) -> None:
    """POST /api/timer/stop when no timer is active returns 409."""
    response = await client.post("/api/timer/stop")

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# GET /api/timer/sessions/{task_id}
# ---------------------------------------------------------------------------


async def test_get_timer_sessions_for_task(
    client: AsyncClient, task: Task
) -> None:
    """GET /api/timer/sessions/{task_id} returns list of TimerSession records."""
    # Complete one full timer cycle to create a session
    await client.post("/api/timer/start", json={"task_id": task.id})
    await client.post("/api/timer/stop")

    response = await client.get(f"/api/timer/sessions/{task.id}")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["task_id"] == task.id
    assert body[0]["duration_seconds"] >= 0


# ---------------------------------------------------------------------------
# POST /api/timer/add-time
# ---------------------------------------------------------------------------


async def test_add_time_creates_session(
    client: AsyncClient, task: Task, db_session: AsyncSession
) -> None:
    """POST /api/timer/add-time creates a TimerSession with the correct duration."""
    from sqlalchemy import select

    response = await client.post(
        "/api/timer/add-time", json={"task_id": task.id, "seconds": 900}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == task.id
    assert body["duration_seconds"] == 900
    assert body["ended_at"] is not None
    assert "id" in body

    # Confirm the session was persisted
    result = await db_session.execute(
        select(TimerSession).where(TimerSession.task_id == task.id)
    )
    sessions = list(result.scalars().all())
    assert len(sessions) == 1
    assert sessions[0].duration_seconds == 900


async def test_add_time_does_not_affect_active_timer(
    client: AsyncClient, task: Task
) -> None:
    """POST /api/timer/add-time leaves any active timer state unchanged."""
    # Start a timer first
    await client.post("/api/timer/start", json={"task_id": task.id})

    # Add manual time
    add_response = await client.post(
        "/api/timer/add-time", json={"task_id": task.id, "seconds": 3600}
    )
    assert add_response.status_code == 200

    # Timer is still running
    current = await client.get("/api/timer/current")
    assert current.json()["status"] == "running"
