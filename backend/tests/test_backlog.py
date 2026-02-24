"""Tests for the /api/backlog endpoints.

Written before the implementation exists (TDD red phase).

Backlog tasks are tasks with day_id=None and category=None.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.models import Day, Task
from app.models.task import (
    CATEGORY_DEEP_WORK,
    CATEGORY_SHORT_TASK,
    STATUS_PENDING,
)


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
    """Insert a Day record and return it for use in tests."""
    d = Day(date=date(2025, 6, 1), created_at=datetime.now(timezone.utc))
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


# ---------------------------------------------------------------------------
# GET /api/backlog - list backlog tasks
# ---------------------------------------------------------------------------


async def test_list_backlog_returns_only_backlog_tasks(
    client: AsyncClient, day: Day
) -> None:
    """GET /api/backlog returns only tasks with day_id=None."""
    # Create a backlog task (day_id not provided)
    await client.post(
        "/api/backlog",
        json={"title": "Backlog task"},
    )

    # Create a regular day task
    await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "Day task"},
    )

    response = await client.get("/api/backlog")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Backlog task"
    assert body[0]["day_id"] is None


async def test_list_backlog_with_tag_filter(client: AsyncClient) -> None:
    """GET /api/backlog?tag=xyz filters by tag name."""
    # Create backlog tasks with different tags
    await client.post(
        "/api/backlog",
        json={"title": "Task with focus tag", "tags": ["focus"]},
    )
    await client.post(
        "/api/backlog",
        json={"title": "Task with other tag", "tags": ["other"]},
    )

    response = await client.get("/api/backlog?tag=focus")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Task with focus tag"
    assert body[0]["tags"] == ["focus"]


async def test_list_backlog_with_search(client: AsyncClient) -> None:
    """GET /api/backlog?search=xyz filters by title substring."""
    await client.post(
        "/api/backlog",
        json={"title": "Important project"},
    )
    await client.post(
        "/api/backlog",
        json={"title": "Random idea"},
    )

    response = await client.get("/api/backlog?search=project")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Important project"


async def test_list_backlog_returns_empty_list_when_no_tasks(
    client: AsyncClient,
) -> None:
    """GET /api/backlog returns [] when no backlog tasks exist."""
    response = await client.get("/api/backlog")

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# POST /api/backlog - create backlog task
# ---------------------------------------------------------------------------


async def test_create_backlog_task(client: AsyncClient) -> None:
    """POST /api/backlog creates a task with day_id=None and category=None."""
    payload = {
        "title": "Future task",
        "description": "Something to do later",
    }
    response = await client.post("/api/backlog", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Future task"
    assert body["description"] == "Something to do later"
    assert body["day_id"] is None
    assert body["category"] is None
    assert body["status"] == STATUS_PENDING
    assert body["order_index"] == 0
    assert body["completed_at"] is None
    assert "id" in body
    assert body["tags"] == []


async def test_create_backlog_task_with_category(client: AsyncClient) -> None:
    """POST /api/backlog creates a task with an optional suggested category."""
    payload = {
        "title": "Suggested deep work",
        "suggested_category": CATEGORY_DEEP_WORK,
    }
    response = await client.post("/api/backlog", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Suggested deep work"
    # Category should be stored as suggested_category
    assert body["category"] == CATEGORY_DEEP_WORK


async def test_create_backlog_task_with_tags(client: AsyncClient) -> None:
    """POST /api/backlog creates a task with tags."""
    payload = {
        "title": "Tagged backlog task",
        "tags": ["focus", "project-x"],
    }
    response = await client.post("/api/backlog", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Tagged backlog task"
    assert set(body["tags"]) == {"focus", "project-x"}


# ---------------------------------------------------------------------------
# POST /api/backlog/{id}/move-to-day - move backlog task to a day
# ---------------------------------------------------------------------------


async def test_move_backlog_task_to_day(client: AsyncClient, day: Day) -> None:
    """POST /api/backlog/{id}/move-to-day moves task from backlog to a day."""
    # Create a backlog task
    create_resp = await client.post(
        "/api/backlog",
        json={"title": "Task to move"},
    )
    task_id = create_resp.json()["id"]

    # Move to day
    move_resp = await client.post(
        f"/api/backlog/{task_id}/move-to-day",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK},
    )

    assert move_resp.status_code == 200
    body = move_resp.json()
    assert body["day_id"] == day.id
    assert body["category"] == CATEGORY_DEEP_WORK
    assert body["title"] == "Task to move"


async def test_move_backlog_task_to_day_uses_existing_category(
    client: AsyncClient, day: Day
) -> None:
    """POST /api/backlog/{id}/move-to-day uses existing category if not provided."""
    # Create a backlog task with a suggested category
    create_resp = await client.post(
        "/api/backlog",
        json={"title": "Pre-categorized task", "suggested_category": CATEGORY_SHORT_TASK},
    )
    task_id = create_resp.json()["id"]

    # Move to day without specifying category
    move_resp = await client.post(
        f"/api/backlog/{task_id}/move-to-day",
        json={"day_id": day.id},
    )

    assert move_resp.status_code == 200
    body = move_resp.json()
    assert body["day_id"] == day.id
    assert body["category"] == CATEGORY_SHORT_TASK


async def test_move_backlog_task_to_day_returns_404_for_nonexistent_task(
    client: AsyncClient, day: Day
) -> None:
    """POST /api/backlog/{id}/move-to-day returns 404 for non-existent task."""
    response = await client.post(
        "/api/backlog/99999/move-to-day",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK},
    )

    assert response.status_code == 404


async def test_move_backlog_task_to_day_removes_from_backlog_list(
    client: AsyncClient, day: Day
) -> None:
    """Moving a task to a day removes it from the backlog list."""
    # Create a backlog task
    create_resp = await client.post(
        "/api/backlog",
        json={"title": "Task to move"},
    )
    task_id = create_resp.json()["id"]

    # Verify it appears in backlog
    list_resp = await client.get("/api/backlog")
    assert len(list_resp.json()) == 1

    # Move to day
    await client.post(
        f"/api/backlog/{task_id}/move-to-day",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK},
    )

    # Verify it no longer appears in backlog
    list_resp = await client.get("/api/backlog")
    assert len(list_resp.json()) == 0


# ---------------------------------------------------------------------------
# POST /api/tasks/{id}/move-to-backlog - move task to backlog
# ---------------------------------------------------------------------------


async def test_move_task_to_backlog(client: AsyncClient, day: Day) -> None:
    """POST /api/tasks/{id}/move-to-backlog moves task from day to backlog."""
    # Create a regular day task
    create_resp = await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "Day task"},
    )
    task_id = create_resp.json()["id"]

    # Move to backlog
    move_resp = await client.post(f"/api/tasks/{task_id}/move-to-backlog")

    assert move_resp.status_code == 200
    body = move_resp.json()
    assert body["day_id"] is None
    assert body["category"] is None
    assert body["title"] == "Day task"


async def test_move_task_to_backlog_returns_404(client: AsyncClient) -> None:
    """POST /api/tasks/{id}/move-to-backlog returns 404 for non-existent task."""
    response = await client.post("/api/tasks/99999/move-to-backlog")

    assert response.status_code == 404


async def test_move_task_to_backlog_appears_in_backlog_list(
    client: AsyncClient, day: Day
) -> None:
    """Moving a task to backlog makes it appear in the backlog list."""
    # Create a regular day task
    create_resp = await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "Day task"},
    )
    task_id = create_resp.json()["id"]

    # Verify backlog is empty
    list_resp = await client.get("/api/backlog")
    assert len(list_resp.json()) == 0

    # Move to backlog
    await client.post(f"/api/tasks/{task_id}/move-to-backlog")

    # Verify it now appears in backlog
    list_resp = await client.get("/api/backlog")
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["title"] == "Day task"


async def test_move_task_to_backlog_preserves_tags(client: AsyncClient, day: Day) -> None:
    """Moving a task to backlog preserves its tags."""
    # Create a task with tags
    create_resp = await client.post(
        "/api/tasks",
        json={
            "day_id": day.id,
            "category": CATEGORY_DEEP_WORK,
            "title": "Tagged task",
            "tags": ["focus", "project"],
        },
    )
    task_id = create_resp.json()["id"]

    # Move to backlog
    move_resp = await client.post(f"/api/tasks/{task_id}/move-to-backlog")

    assert move_resp.status_code == 200
    body = move_resp.json()
    assert set(body["tags"]) == {"focus", "project"}
