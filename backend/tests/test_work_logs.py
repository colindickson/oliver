"""Tests for the WorkLog endpoints.

Covers list and tag-update behaviour, including not-found and edge cases.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Day, WorkLog  # ensure all tables are registered


@pytest.fixture
async def day(db_session: AsyncSession) -> Day:
    """Insert a Day record for use in work-log tests."""
    d = Day(date=date(2025, 7, 1), created_at=datetime.now(timezone.utc))
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


@pytest.fixture
async def work_log(db_session: AsyncSession, day: Day) -> WorkLog:
    """Insert a WorkLog record belonging to ``day``."""
    wl = WorkLog(
        day_id=day.id,
        project_name="Oliver",
        description="Implemented work log tests",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(wl)
    await db_session.commit()
    await db_session.refresh(wl)
    return wl


# ---------------------------------------------------------------------------
# GET /api/days/{date}/work-logs
# ---------------------------------------------------------------------------


async def test_list_work_logs_empty_day(client: AsyncClient, day: Day) -> None:
    """GET /api/days/{date}/work-logs returns [] when day exists but has no work logs."""
    response = await client.get(f"/api/days/{day.date}/work-logs")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_work_logs_nonexistent_day(client: AsyncClient) -> None:
    """GET /api/days/{date}/work-logs returns [] when no Day row exists for the date."""
    response = await client.get("/api/days/2099-12-31/work-logs")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_work_logs_returns_entries(
    client: AsyncClient, day: Day, work_log: WorkLog
) -> None:
    """GET /api/days/{date}/work-logs returns the work log with correct fields."""
    response = await client.get(f"/api/days/{day.date}/work-logs")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    entry = body[0]
    assert entry["id"] == work_log.id
    assert entry["day_id"] == day.id
    assert entry["project_name"] == "Oliver"
    assert entry["description"] == "Implemented work log tests"
    assert entry["tags"] == []
    assert "created_at" in entry


# ---------------------------------------------------------------------------
# PATCH /api/work-logs/{id}/tags
# ---------------------------------------------------------------------------


async def test_update_work_log_tags(
    client: AsyncClient, work_log: WorkLog
) -> None:
    """PATCH /api/work-logs/{id}/tags returns 200 with the updated tag list."""
    response = await client.patch(
        f"/api/work-logs/{work_log.id}/tags",
        json={"tags": ["foo"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == work_log.id
    assert body["tags"] == ["foo"]


async def test_update_work_log_tags_not_found(client: AsyncClient) -> None:
    """PATCH /api/work-logs/99999/tags returns 404 when no work log exists."""
    response = await client.patch(
        "/api/work-logs/99999/tags",
        json={"tags": ["foo"]},
    )
    assert response.status_code == 404
    assert "99999" in response.json()["detail"]


# ---------------------------------------------------------------------------
# DELETE /api/work-logs/{id}
# ---------------------------------------------------------------------------


async def test_delete_work_log_success(client: AsyncClient, work_log: WorkLog, day: Day) -> None:
    """DELETE /api/work-logs/{id} returns 204 and the entry is gone."""
    date_str = day.date.isoformat()
    response = await client.delete(f"/api/work-logs/{work_log.id}")
    assert response.status_code == 204

    list_response = await client.get(f"/api/days/{date_str}/work-logs")
    assert list_response.json() == []


async def test_delete_work_log_not_found(client: AsyncClient) -> None:
    """DELETE /api/work-logs/99999 returns 404 when no work log exists."""
    response = await client.delete("/api/work-logs/99999")
    assert response.status_code == 404
    assert "99999" in response.json()["detail"]


# ---------------------------------------------------------------------------
# PATCH /api/work-logs/{id}
# ---------------------------------------------------------------------------


async def test_update_work_log_project_name(client: AsyncClient, work_log: WorkLog) -> None:
    """PATCH /api/work-logs/{id} updates project_name while leaving description unchanged."""
    response = await client.patch(
        f"/api/work-logs/{work_log.id}",
        json={"project_name": "NewProject"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "NewProject"
    assert data["description"] == work_log.description


async def test_update_work_log_description(client: AsyncClient, work_log: WorkLog) -> None:
    """PATCH /api/work-logs/{id} updates description while leaving project_name unchanged."""
    response = await client.patch(
        f"/api/work-logs/{work_log.id}",
        json={"description": "Updated description"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"
    assert data["project_name"] == work_log.project_name


async def test_update_work_log_not_found(client: AsyncClient) -> None:
    """PATCH /api/work-logs/99999 returns 404 when no work log exists."""
    response = await client.patch(
        "/api/work-logs/99999",
        json={"project_name": "X"},
    )
    assert response.status_code == 404
    assert "99999" in response.json()["detail"]


# ---------------------------------------------------------------------------
# POST /api/work-logs/batch
# ---------------------------------------------------------------------------


async def test_batch_create_work_logs_happy_path(client: AsyncClient) -> None:
    """POST /api/work-logs/batch creates 3 entries across 2 dates, returns them in order."""
    payload = {
        "entries": [
            {"project_name": "oliver", "description": "Entry A", "tags": ["backend"], "date": "2026-01-01"},
            {"project_name": "client-api", "description": "Entry B", "tags": [], "date": "2026-01-02"},
            {"project_name": "oliver", "description": "Entry C", "tags": ["frontend"], "date": "2026-01-01"},
        ]
    }
    response = await client.post("/api/work-logs/batch", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert body[0]["project_name"] == "oliver"
    assert body[0]["description"] == "Entry A"
    assert body[0]["tags"] == ["backend"]
    assert body[1]["project_name"] == "client-api"
    assert body[2]["description"] == "Entry C"
    assert body[0]["day_id"] == body[2]["day_id"]
    assert body[1]["day_id"] != body[0]["day_id"]


async def test_batch_create_work_logs_rejects_excess_tags(client: AsyncClient, db_session: AsyncSession) -> None:
    """POST /api/work-logs/batch returns 400 and saves nothing when any entry exceeds tag limit."""
    from sqlalchemy import select as sa_select
    from app.models import WorkLog as WLModel

    payload = {
        "entries": [
            {"project_name": "good", "description": "Fine entry", "tags": [], "date": "2026-02-01"},
            {"project_name": "bad", "description": "Too many tags", "tags": ["a", "b", "c", "d", "e", "f"], "date": "2026-02-02"},
        ]
    }
    response = await client.post("/api/work-logs/batch", json=payload)
    assert response.status_code == 400

    result = await db_session.execute(sa_select(WLModel))
    assert result.scalars().all() == []


async def test_batch_create_work_logs_empty_entries(client: AsyncClient) -> None:
    """POST /api/work-logs/batch returns 422 when entries list is empty."""
    response = await client.post("/api/work-logs/batch", json={"entries": []})
    assert response.status_code == 422


async def test_batch_create_work_logs_creates_day_rows(client: AsyncClient) -> None:
    """POST /api/work-logs/batch auto-creates Day rows for dates that don't exist yet."""
    payload = {
        "entries": [
            {"project_name": "newday", "description": "No day exists yet", "tags": [], "date": "2030-06-15"},
        ]
    }
    response = await client.post("/api/work-logs/batch", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["project_name"] == "newday"
