"""Tests for the /api/timer endpoints.

Written before the implementation exists (TDD red phase).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Day, Task, TimerSession  # ensure all tables are registered


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


async def test_start_timer_nonexistent_task_returns_404(client: AsyncClient) -> None:
    """POST /api/timer/start with a non-existent task_id returns 404 Not Found."""
    response = await client.post("/api/timer/start", json={"task_id": 999999})

    assert response.status_code == 404


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


async def test_add_time_updates_active_timer_elapsed(
    client: AsyncClient, task: Task
) -> None:
    """POST /api/timer/add-time increments elapsed_seconds of the active timer."""
    # Start a timer first
    await client.post("/api/timer/start", json={"task_id": task.id})

    before = await client.get("/api/timer/current")
    elapsed_before = before.json()["elapsed_seconds"]

    # Add manual time
    add_response = await client.post(
        "/api/timer/add-time", json={"task_id": task.id, "seconds": 3600}
    )
    assert add_response.status_code == 200

    # Timer is still running and elapsed increased by at least 3600
    current = await client.get("/api/timer/current")
    data = current.json()
    assert data["status"] == "running"
    assert data["elapsed_seconds"] >= elapsed_before + 3600


async def test_add_time_rejects_zero_seconds(client: AsyncClient, task: Task) -> None:
    """POST /api/timer/add-time with seconds=0 returns 422 Unprocessable Entity."""
    response = await client.post(
        "/api/timer/add-time", json={"task_id": task.id, "seconds": 0}
    )
    assert response.status_code == 422


async def test_add_time_rejects_negative_seconds(
    client: AsyncClient, task: Task
) -> None:
    """POST /api/timer/add-time with negative seconds returns 422 Unprocessable Entity."""
    response = await client.post(
        "/api/timer/add-time", json={"task_id": task.id, "seconds": -60}
    )
    assert response.status_code == 422


async def test_add_time_invalid_task_returns_404(client: AsyncClient) -> None:
    """POST /api/timer/add-time with a non-existent task_id returns 404."""
    response = await client.post(
        "/api/timer/add-time", json={"task_id": 999999, "seconds": 900}
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Pause -> Stop flow
# ---------------------------------------------------------------------------


async def test_pause_then_stop_creates_session(
    client: AsyncClient, task: Task, db_session: AsyncSession
) -> None:
    """Start -> pause -> stop returns 200 and creates a timer session."""
    from sqlalchemy import select

    await client.post("/api/timer/start", json={"task_id": task.id})
    await client.post("/api/timer/pause")

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


# ---------------------------------------------------------------------------
# Stale timer self-heal (active task deleted out from under the timer)
# ---------------------------------------------------------------------------


async def _delete_task_row(db: AsyncSession, task: Task) -> None:
    from sqlalchemy import delete

    await db.execute(delete(Task).where(Task.id == task.id))
    await db.commit()


async def test_get_current_is_idle_when_active_task_was_deleted(
    client: AsyncClient, db_session: AsyncSession, task: Task
) -> None:
    """Deleting a task by any path (API, MCP, day cascade) must not leave the UI
    showing a running timer for a task that no longer exists."""
    from app.services.timer_service import TimerService

    await client.post("/api/timer/start", json={"task_id": task.id})
    await _delete_task_row(db_session, task)

    current = await TimerService(db_session).get_current()

    assert current["status"] == "idle"
    assert current["task_id"] is None


async def test_stop_with_deleted_active_task_is_409_and_writes_no_session(
    client: AsyncClient, db_session: AsyncSession, task: Task
) -> None:
    """stop() must not insert a TimerSession with a dangling task FK; it behaves
    exactly like stop-while-idle (409)."""
    from sqlalchemy import func, select

    from app.exceptions import InvalidOperationError
    from app.services.timer_service import TimerService

    await client.post("/api/timer/start", json={"task_id": task.id})
    await _delete_task_row(db_session, task)

    with pytest.raises(InvalidOperationError) as exc:
        await TimerService(db_session).stop()

    assert exc.value.http_status_code == 409
    count = await db_session.scalar(select(func.count()).select_from(TimerSession))
    assert count == 0


async def test_start_succeeds_after_active_task_was_deleted(
    client: AsyncClient, db_session: AsyncSession, task: Task
) -> None:
    """A stale running state must not block starting a timer on another task
    ("Timer is already running")."""
    from app.services.timer_service import TimerService

    await client.post("/api/timer/start", json={"task_id": task.id})
    other = Task(day_id=task.day_id, category="deep_work", title="other", order_index=1)
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)
    await _delete_task_row(db_session, task)

    current = await TimerService(db_session).start(other.id)

    assert current["status"] == "running"
    assert current["task_id"] == other.id
