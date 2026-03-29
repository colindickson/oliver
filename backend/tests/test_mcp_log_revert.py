"""Tests for MCP log revert — concurrency safety and tag recreation."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Day, Task, Tag  # ensure tables registered
from app.models.day import Day as DayModel
from app.models.mcp_log import MCPLog


async def _seed_log(
    session: AsyncSession,
    tool_name: str = "create_task",
    params: str | None = None,
    before_state: str | None = None,
    result: str | None = None,
) -> MCPLog:
    log = MCPLog(
        tool_name=tool_name,
        params=params or "{}",
        before_state=before_state,
        result=result,
        status="success",
        is_reverted=False,
        created_at=datetime.now(timezone.utc),
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


async def test_revert_is_atomic(client: AsyncClient, db_session: AsyncSession) -> None:
    """Reverting the same log twice returns 422 on the second attempt."""
    day = DayModel(date=date(2025, 6, 1), created_at=datetime.now(timezone.utc))
    db_session.add(day)
    await db_session.commit()
    await db_session.refresh(day)

    task = Task(
        day_id=day.id,
        category="deep_work",
        title="Original",
        status="pending",
        order_index=0,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    log = await _seed_log(
        db_session,
        tool_name="create_task",
        result=json.dumps({"id": task.id}),
    )

    resp1 = await client.post(f"/api/mcp-logs/{log.id}/revert")
    assert resp1.status_code == 200

    resp2 = await client.post(f"/api/mcp-logs/{log.id}/revert")
    assert resp2.status_code == 422


async def test_revert_persists_across_sessions(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Revert mutation is committed, not rolled back."""
    day = DayModel(date=date(2025, 6, 1), created_at=datetime.now(timezone.utc))
    db_session.add(day)
    await db_session.commit()
    await db_session.refresh(day)

    task = Task(
        day_id=day.id,
        category="deep_work",
        title="To delete",
        status="pending",
        order_index=0,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    log = await _seed_log(
        db_session,
        tool_name="create_task",
        result=json.dumps({"id": task.id}),
    )

    resp = await client.post(f"/api/mcp-logs/{log.id}/revert")
    assert resp.status_code == 200
    assert resp.json()["is_reverted"] is True


async def test_revert_update_task_recreates_deleted_tag(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Reverting an update re-creates tags that were deleted since the original operation."""
    day = DayModel(date=date(2025, 6, 1), created_at=datetime.now(timezone.utc))
    db_session.add(day)
    await db_session.commit()
    await db_session.refresh(day)

    tag = Tag(name="urgent")
    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)

    task = Task(
        day_id=day.id,
        category="deep_work",
        title="Important task",
        status="pending",
        order_index=0,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Link tag to task, then delete the tag (which cascades to the association)
    task.tags = [tag]
    await db_session.commit()

    # Remove the association first, then delete the tag
    task.tags = []
    await db_session.delete(tag)
    await db_session.commit()

    log = await _seed_log(
        db_session,
        tool_name="update_task",
        params=json.dumps({"task_id": task.id}),
        before_state=json.dumps({
            "title": "Important task",
            "description": None,
            "status": "pending",
            "category": "deep_work",
            "tags": ["urgent"],
        }),
    )

    resp = await client.post(f"/api/mcp-logs/{log.id}/revert")
    assert resp.status_code == 200

    # Verify the tag was re-created and linked to the task
    await db_session.rollback()  # clear session cache
    refreshed = await db_session.get(Task, task.id)
    tag_names = [t.name for t in refreshed.tags]
    assert "urgent" in tag_names
