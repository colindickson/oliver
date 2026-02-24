"""Tests for the /api/tasks endpoints.

Written before the implementation exists (TDD red phase).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.models import Day, Task  # ensure all tables are registered
from app.models.task import (
    CATEGORY_DEEP_WORK,
    CATEGORY_SHORT_TASK,
    STATUS_PENDING,
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
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
    """Insert a Day record and return it for use in task tests."""
    d = Day(date=date(2025, 6, 1), created_at=datetime.now(timezone.utc))
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


# ---------------------------------------------------------------------------
# POST /api/tasks
# ---------------------------------------------------------------------------


async def test_create_task(client: AsyncClient, day: Day) -> None:
    """POST /api/tasks creates a task under the correct day."""
    payload = {
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Write unit tests",
        "description": "Cover all edge cases",
        "order_index": 0,
    }
    response = await client.post("/api/tasks", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["day_id"] == day.id
    assert body["category"] == CATEGORY_DEEP_WORK
    assert body["title"] == "Write unit tests"
    assert body["description"] == "Cover all edge cases"
    assert body["status"] == STATUS_PENDING
    assert body["order_index"] == 0
    assert body["completed_at"] is None
    assert "id" in body
    assert body["tags"] == []


async def test_create_task_without_optional_fields(client: AsyncClient, day: Day) -> None:
    """POST /api/tasks succeeds with only required fields provided."""
    payload = {
        "day_id": day.id,
        "category": CATEGORY_SHORT_TASK,
        "title": "Quick win",
    }
    response = await client.post("/api/tasks", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["description"] is None
    assert body["order_index"] == 0


# ---------------------------------------------------------------------------
# GET /api/tasks
# ---------------------------------------------------------------------------


async def test_list_tasks_for_day(client: AsyncClient, day: Day) -> None:
    """GET /api/tasks?day_id=X returns all tasks for that day."""
    # Create two tasks
    for title in ("Task A", "Task B"):
        await client.post(
            "/api/tasks",
            json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": title},
        )

    response = await client.get(f"/api/tasks?day_id={day.id}")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    titles = {t["title"] for t in body}
    assert titles == {"Task A", "Task B"}


async def test_list_tasks_without_filter_returns_all(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /api/tasks without day_id returns every task."""
    day1 = Day(date=date(2025, 6, 1), created_at=datetime.now(timezone.utc))
    day2 = Day(date=date(2025, 6, 2), created_at=datetime.now(timezone.utc))
    db_session.add_all([day1, day2])
    await db_session.commit()
    await db_session.refresh(day1)
    await db_session.refresh(day2)

    for d, title in [(day1, "A"), (day2, "B")]:
        await client.post(
            "/api/tasks",
            json={"day_id": d.id, "category": CATEGORY_DEEP_WORK, "title": title},
        )

    response = await client.get("/api/tasks")

    assert response.status_code == 200
    assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# GET /api/tasks/{id}
# ---------------------------------------------------------------------------


async def test_get_task_by_id(client: AsyncClient, day: Day) -> None:
    """GET /api/tasks/{id} returns the specific task."""
    create_resp = await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "Specific"},
    )
    task_id = create_resp.json()["id"]

    response = await client.get(f"/api/tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["id"] == task_id
    assert response.json()["title"] == "Specific"


async def test_get_task_by_id_returns_404(client: AsyncClient) -> None:
    """GET /api/tasks/{id} returns 404 for a non-existent task."""
    response = await client.get("/api/tasks/99999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/tasks/{id}
# ---------------------------------------------------------------------------


async def test_update_task(client: AsyncClient, day: Day) -> None:
    """PUT /api/tasks/{id} updates title and description."""
    create_resp = await client.post(
        "/api/tasks",
        json={
            "day_id": day.id,
            "category": CATEGORY_DEEP_WORK,
            "title": "Original title",
            "description": "Original desc",
        },
    )
    task_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/tasks/{task_id}",
        json={"title": "Updated title", "description": "Updated desc"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Updated title"
    assert body["description"] == "Updated desc"


async def test_update_task_partial(client: AsyncClient, day: Day) -> None:
    """PUT /api/tasks/{id} with only title updates title and leaves description."""
    create_resp = await client.post(
        "/api/tasks",
        json={
            "day_id": day.id,
            "category": CATEGORY_DEEP_WORK,
            "title": "Old title",
            "description": "Keep me",
        },
    )
    task_id = create_resp.json()["id"]

    response = await client.put(f"/api/tasks/{task_id}", json={"title": "New title"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "New title"
    assert body["description"] == "Keep me"


async def test_update_task_returns_404(client: AsyncClient) -> None:
    """PUT /api/tasks/{id} returns 404 for a non-existent task."""
    response = await client.put("/api/tasks/99999", json={"title": "Ghost"})

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/tasks/{id}
# ---------------------------------------------------------------------------


async def test_delete_task(client: AsyncClient, day: Day) -> None:
    """DELETE /api/tasks/{id} removes the task and returns {"deleted": true}."""
    create_resp = await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "To delete"},
    )
    task_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/tasks/{task_id}")

    assert delete_resp.status_code == 200
    assert delete_resp.json() == {"deleted": True}

    # Confirm it's gone
    get_resp = await client.get(f"/api/tasks/{task_id}")
    assert get_resp.status_code == 404


async def test_delete_task_returns_404(client: AsyncClient) -> None:
    """DELETE /api/tasks/{id} returns 404 for a non-existent task."""
    response = await client.delete("/api/tasks/99999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/tasks/{id}/status
# ---------------------------------------------------------------------------


async def test_patch_status_to_in_progress(client: AsyncClient, day: Day) -> None:
    """PATCH /api/tasks/{id}/status sets status to in_progress."""
    create_resp = await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "Working"},
    )
    task_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/tasks/{task_id}/status", json={"status": STATUS_IN_PROGRESS}
    )

    assert response.status_code == 200
    assert response.json()["status"] == STATUS_IN_PROGRESS
    assert response.json()["completed_at"] is None


async def test_patch_status_to_completed_sets_completed_at(
    client: AsyncClient, day: Day
) -> None:
    """PATCH /api/tasks/{id}/status to completed sets completed_at timestamp."""
    create_resp = await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "Done"},
    )
    task_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/tasks/{task_id}/status", json={"status": STATUS_COMPLETED}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == STATUS_COMPLETED
    assert body["completed_at"] is not None


async def test_patch_status_returns_404(client: AsyncClient) -> None:
    """PATCH /api/tasks/{id}/status returns 404 for a non-existent task."""
    response = await client.patch("/api/tasks/99999/status", json={"status": STATUS_PENDING})

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/tasks/reorder
# ---------------------------------------------------------------------------


async def test_reorder_tasks(client: AsyncClient, day: Day) -> None:
    """POST /api/tasks/reorder updates order_index values per list position."""
    ids = []
    for title in ("First", "Second", "Third"):
        resp = await client.post(
            "/api/tasks",
            json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": title},
        )
        ids.append(resp.json()["id"])

    # Reverse the order
    reversed_ids = list(reversed(ids))
    reorder_resp = await client.post("/api/tasks/reorder", json={"task_ids": reversed_ids})

    assert reorder_resp.status_code == 200
    assert reorder_resp.json() == {"reordered": True}

    # Verify the new order_index values
    for expected_index, task_id in enumerate(reversed_ids):
        get_resp = await client.get(f"/api/tasks/{task_id}")
        assert get_resp.json()["order_index"] == expected_index


# ---------------------------------------------------------------------------
# POST /api/tasks/{task_id}/continue-tomorrow
# ---------------------------------------------------------------------------


async def test_continue_tomorrow_marks_original_completed(
    client: AsyncClient, day: Day
) -> None:
    """continue-tomorrow sets the original task status to completed."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Deep focus block",
        "description": "Work on the thing",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    resp = await client.post(f"/api/tasks/{task_id}/continue-tomorrow")

    assert resp.status_code == 200
    # Verify original is now completed
    original_resp = await client.get(f"/api/tasks/{task_id}")
    assert original_resp.json()["status"] == STATUS_COMPLETED
    assert original_resp.json()["completed_at"] is not None


async def test_continue_tomorrow_creates_copy_on_next_day(
    client: AsyncClient, day: Day
) -> None:
    """continue-tomorrow returns a new pending deep_work task for tomorrow."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Deep focus block",
        "description": "Work on the thing",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    resp = await client.post(f"/api/tasks/{task_id}/continue-tomorrow")

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] != task_id
    assert body["title"] == "Deep focus block"
    assert body["description"] == "Work on the thing"
    assert body["category"] == CATEGORY_DEEP_WORK
    assert body["status"] == STATUS_PENDING
    assert body["completed_at"] is None

    # Verify the new task is on tomorrow's day
    tomorrow_str = str(date.today() + timedelta(days=1))
    day_resp = await client.get(f"/api/days/{tomorrow_str}")
    assert day_resp.status_code == 200
    assert day_resp.json()["id"] == body["day_id"]


async def test_continue_tomorrow_copies_tags(
    client: AsyncClient, day: Day
) -> None:
    """continue-tomorrow carries tags over to the new task."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Tagged task",
        "order_index": 0,
        "tags": ["focus", "project-x"],
    })
    assert sorted(create_resp.json()["tags"]) == ["focus", "project-x"], "Precondition: tags must be persisted on create"
    task_id = create_resp.json()["id"]

    resp = await client.post(f"/api/tasks/{task_id}/continue-tomorrow")

    assert resp.status_code == 200
    assert sorted(resp.json()["tags"]) == ["focus", "project-x"]


async def test_continue_tomorrow_404_for_missing_task(
    client: AsyncClient,
) -> None:
    """continue-tomorrow returns 404 when the task does not exist."""
    resp = await client.post("/api/tasks/99999/continue-tomorrow")
    assert resp.status_code == 404


async def test_continue_tomorrow_rejects_non_deep_work_task(
    client: AsyncClient, day: Day
) -> None:
    """continue-tomorrow returns 422 for tasks that are not deep_work."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_SHORT_TASK,
        "title": "Quick email",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    resp = await client.post(f"/api/tasks/{task_id}/continue-tomorrow")

    assert resp.status_code == 422
    assert "deep_work" in resp.json()["detail"]
