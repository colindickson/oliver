"""Tests for the /api/goals endpoints."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import Goal, Tag, Task  # ensure all tables registered
from app.models.day import Day

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
    """Insert a Day record."""
    d = Day(date=date(2025, 6, 1), created_at=datetime.now(timezone.utc))
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


@pytest.fixture
async def task(db_session: AsyncSession, day: Day) -> Task:
    """Insert a Task on the test day."""
    t = Task(day_id=day.id, category="short_task", title="Test task", status="pending", order_index=0)
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest.fixture
async def tag(db_session: AsyncSession) -> Tag:
    """Insert a Tag."""
    tg = Tag(name="work")
    db_session.add(tg)
    await db_session.commit()
    await db_session.refresh(tg)
    return tg


# ---------------------------------------------------------------------------
# POST /api/goals
# ---------------------------------------------------------------------------


async def test_create_goal(client: AsyncClient) -> None:
    """Basic goal creation returns expected shape."""
    resp = await client.post("/api/goals", json={"title": "Ship v1"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Ship v1"
    assert data["status"] == "active"
    assert data["total_tasks"] == 0
    assert data["completed_tasks"] == 0
    assert data["progress_pct"] == 0
    assert data["tags"] == []


async def test_create_goal_with_tags(client: AsyncClient, task: Task, tag: Tag, db_session: AsyncSession) -> None:
    """Goal created with tag_names links those tags."""
    # Link tag to task so it shows up in progress
    task.tags = [tag]
    await db_session.commit()

    resp = await client.post("/api/goals", json={"title": "Tagged goal", "tag_names": ["work"]})
    assert resp.status_code == 201
    data = resp.json()
    assert "work" in data["tags"]
    # The task with tag 'work' counts toward progress
    assert data["total_tasks"] == 1


# ---------------------------------------------------------------------------
# Progress computation
# ---------------------------------------------------------------------------


async def test_goal_progress_via_tags(client: AsyncClient, task: Task, tag: Tag, db_session: AsyncSession) -> None:
    """Tasks linked via a shared tag appear in goal progress."""
    task.tags = [tag]
    await db_session.commit()

    resp = await client.post("/api/goals", json={"title": "Tag goal", "tag_names": ["work"]})
    data = resp.json()
    assert data["total_tasks"] == 1
    assert data["completed_tasks"] == 0
    assert data["progress_pct"] == 0


async def test_goal_progress_via_direct_tasks(client: AsyncClient, task: Task) -> None:
    """Tasks linked directly appear in goal progress."""
    resp = await client.post("/api/goals", json={"title": "Direct goal", "task_ids": [task.id]})
    assert resp.status_code == 201
    data = resp.json()
    assert data["total_tasks"] == 1
    assert data["completed_tasks"] == 0


async def test_deduplication(client: AsyncClient, task: Task, tag: Tag, db_session: AsyncSession) -> None:
    """A task linked via both tag and direct_tasks is counted once."""
    task.tags = [tag]
    await db_session.commit()

    resp = await client.post(
        "/api/goals",
        json={"title": "Dedup goal", "tag_names": ["work"], "task_ids": [task.id]},
    )
    data = resp.json()
    assert data["total_tasks"] == 1  # not 2


# ---------------------------------------------------------------------------
# Auto-complete
# ---------------------------------------------------------------------------


async def test_auto_complete(client: AsyncClient, task: Task, db_session: AsyncSession) -> None:
    """Completing all linked tasks auto-completes the goal."""
    # Create goal with direct task
    create_resp = await client.post("/api/goals", json={"title": "Auto complete", "task_ids": [task.id]})
    goal_id = create_resp.json()["id"]

    # Complete the task
    task.status = "completed"
    await db_session.commit()

    # Update goal (trigger auto-complete check)
    update_resp = await client.put(f"/api/goals/{goal_id}", json={"title": "Auto complete"})
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["status"] == "completed"
    assert data["completed_at"] is not None


# ---------------------------------------------------------------------------
# Manual status transitions
# ---------------------------------------------------------------------------


async def test_manual_complete(client: AsyncClient) -> None:
    """Manually marking a goal done works even with no tasks."""
    create_resp = await client.post("/api/goals", json={"title": "Manual done"})
    goal_id = create_resp.json()["id"]

    resp = await client.patch(f"/api/goals/{goal_id}/status", json={"status": "completed"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["completed_at"] is not None


async def test_reopen_goal(client: AsyncClient) -> None:
    """Reopening a completed goal clears completed_at and sets status to active."""
    create_resp = await client.post("/api/goals", json={"title": "Reopen me"})
    goal_id = create_resp.json()["id"]

    await client.patch(f"/api/goals/{goal_id}/status", json={"status": "completed"})
    resp = await client.patch(f"/api/goals/{goal_id}/status", json={"status": "active"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active"
    assert data["completed_at"] is None


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


async def test_update_goal_tags(client: AsyncClient, tag: Tag) -> None:
    """Updating tag_names replaces the goal's tag list."""
    create_resp = await client.post("/api/goals", json={"title": "Tag update", "tag_names": ["work"]})
    goal_id = create_resp.json()["id"]
    assert "work" in create_resp.json()["tags"]

    # Replace with no tags
    resp = await client.put(f"/api/goals/{goal_id}", json={"tag_names": []})
    assert resp.status_code == 200
    assert resp.json()["tags"] == []


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


async def test_delete_goal(client: AsyncClient, task: Task, tag: Tag, db_session: AsyncSession) -> None:
    """Deleting a goal removes it but NOT the linked tasks or tags."""
    task.tags = [tag]
    await db_session.commit()

    create_resp = await client.post(
        "/api/goals",
        json={"title": "Delete me", "tag_names": ["work"], "task_ids": [task.id]},
    )
    goal_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/goals/{goal_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

    # Goal is gone
    get_resp = await client.get(f"/api/goals/{goal_id}")
    assert get_resp.status_code == 404

    # Tasks and tags still exist
    from sqlalchemy import select
    task_result = await db_session.execute(select(Task).where(Task.id == task.id))
    assert task_result.scalar_one_or_none() is not None

    tag_result = await db_session.execute(select(Tag).where(Tag.id == tag.id))
    assert tag_result.scalar_one_or_none() is not None


# ---------------------------------------------------------------------------
# GET endpoints
# ---------------------------------------------------------------------------


async def test_list_goals(client: AsyncClient) -> None:
    """GET /api/goals returns all goals."""
    await client.post("/api/goals", json={"title": "Goal A"})
    await client.post("/api/goals", json={"title": "Goal B"})

    resp = await client.get("/api/goals")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_get_goal_detail(client: AsyncClient, task: Task) -> None:
    """GET /api/goals/{id} returns full task list."""
    create_resp = await client.post("/api/goals", json={"title": "Detail goal", "task_ids": [task.id]})
    goal_id = create_resp.json()["id"]

    resp = await client.get(f"/api/goals/{goal_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "tasks" in data
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["id"] == task.id
