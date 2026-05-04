"""Tests for the /api/tasks endpoints.

Written before the implementation exists (TDD red phase).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Day, Task  # ensure all tables are registered
from app.models.task import (
    CATEGORY_DEEP_WORK,
    CATEGORY_SHORT_TASK,
    STATUS_PENDING,
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
)
from oliver_shared import STATUS_ROLLED_FORWARD
from oliver_shared import CATEGORY_MAINTENANCE  # noqa: F401
from app.services.day_service import DayService


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

    assert response.status_code == 201
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

    assert response.status_code == 201
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
# POST /api/tasks/{task_id}/continue
# ---------------------------------------------------------------------------


async def test_continue_marks_original_completed(
    client: AsyncClient, day: Day
) -> None:
    """POST /continue sets the original task status to completed."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Deep focus block",
        "description": "Work on the thing",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    resp = await client.post(f"/api/tasks/{task_id}/continue")

    assert resp.status_code == 200
    original_resp = await client.get(f"/api/tasks/{task_id}")
    assert original_resp.json()["status"] == STATUS_COMPLETED
    assert original_resp.json()["completed_at"] is not None


async def test_continue_creates_copy_on_next_day(
    client: AsyncClient, day: Day
) -> None:
    """POST /continue returns a new pending task for the next working day."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Deep focus block",
        "description": "Work on the thing",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    resp = await client.post(f"/api/tasks/{task_id}/continue")

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] != task_id
    assert body["title"] == "Deep focus block"
    assert body["description"] == "Work on the thing"
    assert body["category"] == CATEGORY_DEEP_WORK
    assert body["status"] == STATUS_PENDING
    assert body["completed_at"] is None
    assert body["rolled_from_task_id"] == task_id


async def test_continue_copies_tags(
    client: AsyncClient, day: Day
) -> None:
    """POST /continue carries tags over to the new task."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Tagged task",
        "order_index": 0,
        "tags": ["focus", "project-x"],
    })
    assert sorted(create_resp.json()["tags"]) == ["focus", "project-x"]
    task_id = create_resp.json()["id"]

    resp = await client.post(f"/api/tasks/{task_id}/continue")

    assert resp.status_code == 200
    assert sorted(resp.json()["tags"]) == ["focus", "project-x"]


async def test_continue_404_for_missing_task(client: AsyncClient) -> None:
    """POST /continue returns 404 when the task does not exist."""
    resp = await client.post("/api/tasks/99999/continue")
    assert resp.status_code == 404


async def test_continue_task_non_deep_work_succeeds(
    client: AsyncClient, day: Day
) -> None:
    """POST /continue works for all task types, not just deep_work."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_SHORT_TASK,
        "title": "Quick email",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    resp = await client.post(f"/api/tasks/{task_id}/continue")

    assert resp.status_code == 200
    assert resp.json()["category"] == CATEGORY_SHORT_TASK


# ---------------------------------------------------------------------------
# POST /api/tasks/{task_id}/continue — next working day logic
# ---------------------------------------------------------------------------


async def test_continue_skips_weekend_with_recurring_days_off(
    client: AsyncClient, day: Day, db_session: AsyncSession
) -> None:
    """Friday + weekends recurring off → task lands on Monday."""
    friday = date(2025, 6, 6)  # Known Friday

    day_service = DayService(db_session)
    await day_service.set_recurring_days_off(["saturday", "sunday"])
    await db_session.commit()

    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Friday deep work",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    with patch("app.services.day_service.date") as mock_date:
        mock_date.today.return_value = friday
        resp = await client.post(f"/api/tasks/{task_id}/continue")

    assert resp.status_code == 200
    monday = date(2025, 6, 9)
    day_resp = await client.get(f"/api/days/{monday}")
    assert day_resp.status_code == 200
    assert day_resp.json()["id"] == resp.json()["day_id"]


async def test_continue_lands_on_saturday_without_recurring_days_off(
    client: AsyncClient, day: Day
) -> None:
    """Friday + no recurring days off → task lands on Saturday."""
    friday = date(2025, 6, 6)  # Known Friday

    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Friday deep work",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    with patch("app.services.day_service.date") as mock_date:
        mock_date.today.return_value = friday
        resp = await client.post(f"/api/tasks/{task_id}/continue")

    assert resp.status_code == 200
    saturday = date(2025, 6, 7)
    day_resp = await client.get(f"/api/days/{saturday}")
    assert day_resp.status_code == 200
    assert day_resp.json()["id"] == resp.json()["day_id"]


async def test_continue_skips_individual_day_off(
    client: AsyncClient, day: Day, db_session: AsyncSession
) -> None:
    """Tomorrow individually marked as day off → task skips to the day after."""
    today = date(2025, 6, 2)  # Monday
    tomorrow = date(2025, 6, 3)  # Tuesday — will be marked as day off

    day_service = DayService(db_session)
    tomorrow_day = await day_service.get_or_create_by_date(tomorrow)
    await day_service.upsert_day_off(tomorrow_day.id, "sick_day", None)
    await db_session.commit()

    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Monday deep work",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    with patch("app.services.day_service.date") as mock_date:
        mock_date.today.return_value = today
        resp = await client.post(f"/api/tasks/{task_id}/continue")

    assert resp.status_code == 200
    wednesday = date(2025, 6, 4)
    day_resp = await client.get(f"/api/days/{wednesday}")
    assert day_resp.status_code == 200
    assert day_resp.json()["id"] == resp.json()["day_id"]


# ---------------------------------------------------------------------------
# POST /api/tasks/{task_id}/continue — with explicit target_date
# ---------------------------------------------------------------------------


async def test_continue_with_target_date_creates_task_on_target_day(
    client: AsyncClient, day: Day
) -> None:
    """POST /continue with target_date creates a new task on the specified future date."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_SHORT_TASK,
        "title": "Pending task",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    future_date = (date.today() + timedelta(days=3)).isoformat()
    resp = await client.post(f"/api/tasks/{task_id}/continue", json={"target_date": future_date})

    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Pending task"
    assert body["status"] == STATUS_PENDING
    assert body["rolled_from_task_id"] == task_id
    assert body["rolled_from_date"] is not None


async def test_continue_with_target_date_marks_original_completed(
    client: AsyncClient, day: Day
) -> None:
    """POST /continue marks the original task completed (not rolled_forward)."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_SHORT_TASK,
        "title": "Incomplete task",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    future_date = (date.today() + timedelta(days=2)).isoformat()
    await client.post(f"/api/tasks/{task_id}/continue", json={"target_date": future_date})

    original_resp = await client.get(f"/api/tasks/{task_id}")
    assert original_resp.status_code == 200
    assert original_resp.json()["status"] == STATUS_COMPLETED


async def test_continue_with_target_date_sets_rolled_from_task_id(
    client: AsyncClient, day: Day
) -> None:
    """New task has rolled_from_task_id pointing to the original."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Original",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    future_date = (date.today() + timedelta(days=1)).isoformat()
    resp = await client.post(f"/api/tasks/{task_id}/continue", json={"target_date": future_date})

    assert resp.json()["rolled_from_task_id"] == task_id


async def test_continue_rejects_completed_task(
    client: AsyncClient, day: Day
) -> None:
    """POST /continue on a completed task returns 422."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_SHORT_TASK,
        "title": "Done task",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    await client.patch(f"/api/tasks/{task_id}/status", json={"status": STATUS_COMPLETED})

    resp = await client.post(f"/api/tasks/{task_id}/continue")

    assert resp.status_code == 422


async def test_continue_task_rejects_terminal_status(
    client: AsyncClient, day: Day
) -> None:
    """POST /continue on a rolled_forward task also returns 422."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_SHORT_TASK,
        "title": "Rolled task",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    # Continue it once so original becomes completed
    future_date = (date.today() + timedelta(days=2)).isoformat()
    await client.post(f"/api/tasks/{task_id}/continue", json={"target_date": future_date})

    # Verify original is now completed
    original_resp = await client.get(f"/api/tasks/{task_id}")
    assert original_resp.json()["status"] == STATUS_COMPLETED

    # Attempting to continue the completed original should fail
    resp = await client.post(f"/api/tasks/{task_id}/continue")
    assert resp.status_code == 422


async def test_continue_with_target_date_rejects_past_date(
    client: AsyncClient, day: Day
) -> None:
    """POST /continue with a past target_date returns 400."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_SHORT_TASK,
        "title": "Task",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    past_date = (date.today() - timedelta(days=1)).isoformat()
    resp = await client.post(f"/api/tasks/{task_id}/continue", json={"target_date": past_date})

    assert resp.status_code == 400


async def test_continue_task_rejects_already_continued(
    client: AsyncClient, day: Day
) -> None:
    """POST /continue on a task that already has a continuation returns 422."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_SHORT_TASK,
        "title": "Source",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    future_date = (date.today() + timedelta(days=2)).isoformat()
    await client.post(f"/api/tasks/{task_id}/continue", json={"target_date": future_date})

    # Task is now completed. The further_date test is now about terminal status.
    # Use the new continuation task itself as the one to double-continue.
    # The original is completed — try a fresh task to test already-continued separately.
    create_resp2 = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_SHORT_TASK,
        "title": "Source 2",
        "order_index": 0,
    })
    task_id2 = create_resp2.json()["id"]

    date_1 = (date.today() + timedelta(days=2)).isoformat()
    continue_resp = await client.post(f"/api/tasks/{task_id2}/continue", json={"target_date": date_1})
    new_task_id = continue_resp.json()["id"]

    # The new (continued) task has been continued once from original.
    # Try to continue the original again (now completed) — should fail with 422
    resp = await client.post(f"/api/tasks/{task_id2}/continue")
    assert resp.status_code == 422  # terminal status

    # Try to continue the continuation task twice (it hasn't been continued yet)
    date_2 = (date.today() + timedelta(days=4)).isoformat()
    await client.post(f"/api/tasks/{new_task_id}/continue", json={"target_date": date_2})

    # Now try to continue new_task_id again — it's been continued (has rolled_to)
    date_3 = (date.today() + timedelta(days=6)).isoformat()
    resp2 = await client.post(f"/api/tasks/{new_task_id}/continue", json={"target_date": date_3})
    assert resp2.status_code == 422


async def test_continue_chain(
    client: AsyncClient, day: Day
) -> None:
    """A → B → C chaining: each original becomes completed."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_MAINTENANCE,
        "title": "Chain start",
        "order_index": 0,
    })
    task_a_id = create_resp.json()["id"]

    date_b = (date.today() + timedelta(days=1)).isoformat()
    resp_b = await client.post(f"/api/tasks/{task_a_id}/continue", json={"target_date": date_b})

    assert resp_b.status_code == 200
    task_b_id = resp_b.json()["id"]
    assert task_b_id != task_a_id

    date_c = (date.today() + timedelta(days=3)).isoformat()
    resp_c = await client.post(f"/api/tasks/{task_b_id}/continue", json={"target_date": date_c})

    assert resp_c.status_code == 200
    task_c = resp_c.json()
    assert task_c["rolled_from_task_id"] == task_b_id

    task_a_resp = await client.get(f"/api/tasks/{task_a_id}")
    assert task_a_resp.json()["status"] == STATUS_COMPLETED

    task_b_resp = await client.get(f"/api/tasks/{task_b_id}")
    assert task_b_resp.json()["status"] == STATUS_COMPLETED


# ---------------------------------------------------------------------------
# Response building consistency — ensure roll relationships are enriched
# ---------------------------------------------------------------------------


async def test_continue_response_includes_rolled_from_date(client: AsyncClient, day: Day) -> None:
    """POST /continue response includes rolled_from_date when task has roll relationship."""
    create_resp = await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "Work", "tags": []},
    )
    task_id = create_resp.json()["id"]

    future_date = (date.today() + timedelta(days=2)).isoformat()
    continue_resp = await client.post(
        f"/api/tasks/{task_id}/continue", json={"target_date": future_date}
    )

    assert continue_resp.status_code == 200
    new_task = continue_resp.json()
    assert "rolled_from_date" in new_task
    assert new_task["rolled_from_date"] == day.date.isoformat()


async def test_continue_returns_consistent_response(client: AsyncClient, day: Day) -> None:
    """POST /continue response has the same enriched TaskResponse shape."""
    create_resp = await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "Deep work", "tags": []},
    )
    task_id = create_resp.json()["id"]

    continue_resp = await client.post(f"/api/tasks/{task_id}/continue")

    assert continue_resp.status_code == 200
    new_task = continue_resp.json()
    assert new_task["rolled_from_task_id"] == task_id
    assert new_task.get("rolled_from_date") is not None


# ---------------------------------------------------------------------------
# TaskService.continue_task() — service-level method
# ---------------------------------------------------------------------------


async def test_task_service_continue_creates_task(db_session: AsyncSession, day: Day) -> None:
    """TaskService.continue_task() creates a new task on the next working day."""
    from app.services.task_service import TaskService

    task = Task(
        day_id=day.id,
        category=CATEGORY_DEEP_WORK,
        title="Deep focus",
        status=STATUS_PENDING,
        order_index=0,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    service = TaskService(db_session)
    _, new_task = await service.continue_task(task.id)

    assert new_task.id != task.id
    assert new_task.title == task.title
    assert new_task.status == STATUS_PENDING
    assert new_task.day_id != task.day_id
    assert new_task.rolled_from_task_id == task.id


async def test_task_service_continue_marks_original_completed(
    db_session: AsyncSession, day: Day
) -> None:
    """TaskService.continue_task() marks original task completed."""
    from app.services.task_service import TaskService

    task = Task(
        day_id=day.id,
        category=CATEGORY_DEEP_WORK,
        title="Work",
        status=STATUS_PENDING,
        order_index=0,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    service = TaskService(db_session)
    await service.continue_task(task.id)

    await db_session.refresh(task)
    assert task.status == STATUS_COMPLETED
    assert task.completed_at is not None


async def test_task_service_continue_copies_tags(
    db_session: AsyncSession, day: Day
) -> None:
    """TaskService.continue_task() preserves tags on the new task."""
    from app.models.tag import Tag
    from app.services.task_service import TaskService

    tag1 = Tag(name="focus")
    tag2 = Tag(name="urgent")
    db_session.add(tag1)
    db_session.add(tag2)
    await db_session.flush()

    task = Task(
        day_id=day.id,
        category=CATEGORY_DEEP_WORK,
        title="Tagged work",
        status=STATUS_PENDING,
        order_index=0,
    )
    task.tags = [tag1, tag2]
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    service = TaskService(db_session)
    _, new_task = await service.continue_task(task.id)

    assert {t.name for t in new_task.tags} == {"focus", "urgent"}


async def test_continue_task_without_target_date_uses_next_working_day(
    db_session: AsyncSession, day: Day
) -> None:
    """TaskService.continue_task() with no date uses get_next_working_day()."""
    from app.services.task_service import TaskService

    friday = date(2025, 6, 6)
    day_service = DayService(db_session)
    await day_service.set_recurring_days_off(["saturday", "sunday"])
    await db_session.commit()

    task = Task(
        day_id=day.id,
        category=CATEGORY_SHORT_TASK,
        title="Any task",
        status=STATUS_PENDING,
        order_index=0,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    service = TaskService(db_session)

    with patch("app.services.day_service.date") as mock_date:
        mock_date.today.return_value = friday
        _, new_task = await service.continue_task(task.id)

    monday = date(2025, 6, 9)
    target_day = await day_service.get_or_create_by_date(monday)
    assert new_task.day_id == target_day.id


async def test_task_service_continue_raises_task_not_found_error(
    db_session: AsyncSession,
) -> None:
    """TaskService.continue_task() raises TaskNotFoundError for a missing task id."""
    from app.exceptions import TaskNotFoundError
    from app.services.task_service import TaskService

    service = TaskService(db_session)
    with pytest.raises(TaskNotFoundError):
        await service.continue_task(99999)


async def test_task_service_continue_rejects_completed_task(
    db_session: AsyncSession, day: Day
) -> None:
    """TaskService.continue_task() raises InvalidOperationError for completed tasks."""
    from app.exceptions import InvalidOperationError
    from app.services.task_service import TaskService

    task = Task(
        day_id=day.id,
        category=CATEGORY_DEEP_WORK,
        title="Done work",
        status=STATUS_COMPLETED,
        order_index=0,
        completed_at=datetime.now(timezone.utc),
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    service = TaskService(db_session)
    target_date = date.today() + timedelta(days=2)

    with pytest.raises(InvalidOperationError) as exc_info:
        await service.continue_task(task.id, target_date)

    assert "terminal" in str(exc_info.value).lower()


async def test_task_service_continue_rejects_past_date(
    db_session: AsyncSession, day: Day
) -> None:
    """TaskService.continue_task() raises InvalidOperationError (400) for past dates."""
    from app.exceptions import InvalidOperationError
    from app.services.task_service import TaskService

    task = Task(
        day_id=day.id,
        category=CATEGORY_DEEP_WORK,
        title="Work",
        status=STATUS_PENDING,
        order_index=0,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    service = TaskService(db_session)
    past_date = date.today() - timedelta(days=1)

    with pytest.raises(InvalidOperationError) as exc_info:
        await service.continue_task(task.id, past_date)

    assert exc_info.value.http_status_code == 400
    assert "future" in str(exc_info.value).lower()
