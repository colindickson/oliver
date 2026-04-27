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
