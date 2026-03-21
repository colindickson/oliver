"""Tests for the /api/tags endpoints and tag behaviour on tasks.

Written in TDD style — tests define expected behaviour before verifying
the implementation satisfies them.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Day, Tag, Task  # ensure all tables are registered
from app.models.task import CATEGORY_DEEP_WORK


@pytest.fixture
async def day(db_session: AsyncSession) -> Day:
    """Insert a Day record and return it for use in task tests."""
    d = Day(date=date(2025, 6, 1), created_at=datetime.now(timezone.utc))
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


@pytest.fixture
async def day2(db_session: AsyncSession) -> Day:
    """Insert a second Day record on a different date."""
    d = Day(date=date(2025, 6, 2), created_at=datetime.now(timezone.utc))
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


# ---------------------------------------------------------------------------
# GET /api/tags
# ---------------------------------------------------------------------------


async def test_list_tags_empty(client: AsyncClient) -> None:
    """GET /api/tags returns [] when no tags exist."""
    response = await client.get("/api/tags")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# POST /api/tasks with tags
# ---------------------------------------------------------------------------


async def test_create_task_with_tags(client: AsyncClient, day: Day) -> None:
    """Creating a task with tags returns those tags in the response."""
    payload = {
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Focused work",
        "tags": ["focus"],
    }
    response = await client.post("/api/tasks", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["tags"] == ["focus"]


async def test_tags_normalized(client: AsyncClient, day: Day) -> None:
    """Tags are stored lowercase and trimmed regardless of input casing."""
    payload = {
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Test normalisation",
        "tags": ["  Focus  "],
    }
    response = await client.post("/api/tasks", json=payload)
    assert response.status_code == 200
    assert response.json()["tags"] == ["focus"]


async def test_max_tags_enforced(client: AsyncClient, day: Day) -> None:
    """Creating a task with 6+ tags returns HTTP 400."""
    payload = {
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Too many tags",
        "tags": ["a", "b", "c", "d", "e", "f"],
    }
    response = await client.post("/api/tasks", json=payload)
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# PUT /api/tasks/{id} — tag update behaviour
# ---------------------------------------------------------------------------


async def test_update_replaces_tags(client: AsyncClient, day: Day) -> None:
    """Updating a task with a new tag list replaces the old list."""
    # Create with tag "a"
    create_resp = await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "T", "tags": ["a"]},
    )
    task_id = create_resp.json()["id"]

    # Update with tag "b"
    update_resp = await client.put(f"/api/tasks/{task_id}", json={"tags": ["b"]})
    assert update_resp.status_code == 200
    assert update_resp.json()["tags"] == ["b"]


async def test_update_no_tags_field_preserves_tags(client: AsyncClient, day: Day) -> None:
    """Updating a task without a 'tags' key leaves existing tags untouched."""
    create_resp = await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "T", "tags": ["keep"]},
    )
    task_id = create_resp.json()["id"]

    # Update title only — no tags key
    update_resp = await client.put(f"/api/tasks/{task_id}", json={"title": "Updated"})
    assert update_resp.status_code == 200
    assert update_resp.json()["tags"] == ["keep"]


# ---------------------------------------------------------------------------
# GET /api/tags/{tag_name}/tasks
# ---------------------------------------------------------------------------


async def test_get_tasks_for_tag(client: AsyncClient, day: Day, day2: Day) -> None:
    """Tasks with a given tag are returned grouped by day, newest first."""
    await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "Task A", "tags": ["ai"]},
    )
    await client.post(
        "/api/tasks",
        json={"day_id": day2.id, "category": CATEGORY_DEEP_WORK, "title": "Task B", "tags": ["ai"]},
    )

    response = await client.get("/api/tags/ai/tasks")
    assert response.status_code == 200
    groups = response.json()
    # Two groups, newest date first
    assert len(groups) == 2
    assert groups[0]["date"] == "2025-06-02"
    assert groups[1]["date"] == "2025-06-01"
    assert len(groups[0]["tasks"]) == 1
    assert len(groups[1]["tasks"]) == 1


async def test_get_tasks_for_tag_includes_backlog(client: AsyncClient, day: Day) -> None:
    """Backlog tasks (no day_id) with a given tag appear under a 'backlog' group."""
    # Day-assigned task
    await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "Day Task", "tags": ["ai"]},
    )
    # Backlog task via backlog endpoint (day_id=NULL)
    await client.post(
        "/api/backlog",
        json={"title": "Backlog Task", "tags": ["ai"]},
    )

    response = await client.get("/api/tags/ai/tasks")
    assert response.status_code == 200
    groups = response.json()

    dates = [g["date"] for g in groups]
    assert "backlog" in dates

    backlog_group = next(g for g in groups if g["date"] == "backlog")
    assert len(backlog_group["tasks"]) == 1
    assert backlog_group["tasks"][0]["title"] == "Backlog Task"


async def test_get_nonexistent_tag(client: AsyncClient) -> None:
    """GET /api/tags/{tag_name}/tasks returns 404 for an unknown tag."""
    response = await client.get("/api/tags/nonexistent/tasks")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Orphaned tags (tags with 0 tasks) should not appear in list
# ---------------------------------------------------------------------------


async def test_orphaned_tags_not_listed(client: AsyncClient, day: Day) -> None:
    """Tags with no associated tasks should not appear in GET /api/tags."""
    # Create a task with tag "temporary"
    create_resp = await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "T", "tags": ["temporary"]},
    )
    assert create_resp.status_code == 200

    # Verify tag appears in list
    list_resp = await client.get("/api/tags")
    tag_names = [t["name"] for t in list_resp.json()]
    assert "temporary" in tag_names

    # Remove all tags from the task (making "temporary" orphaned)
    task_id = create_resp.json()["id"]
    update_resp = await client.put(f"/api/tasks/{task_id}", json={"tags": []})
    assert update_resp.status_code == 200

    # Now the orphaned tag should NOT appear in the list
    list_resp = await client.get("/api/tags")
    tag_names = [t["name"] for t in list_resp.json()]
    assert "temporary" not in tag_names


# ---------------------------------------------------------------------------
# TagService.resolve_tags() — utility method for resolving multiple tag names
# ---------------------------------------------------------------------------


async def test_resolve_tags_creates_and_returns_tags(db_session: AsyncSession) -> None:
    """resolve_tags returns Tag objects for given names, creating missing ones."""
    from app.services.tag_service import TagService

    service = TagService(db_session)
    tags = await service.resolve_tags(["focus", "urgent"])

    assert len(tags) == 2
    assert {t.name for t in tags} == {"focus", "urgent"}


async def test_resolve_tags_empty_list(db_session: AsyncSession) -> None:
    """resolve_tags with empty list returns empty list."""
    from app.services.tag_service import TagService

    service = TagService(db_session)
    tags = await service.resolve_tags([])

    assert tags == []


async def test_resolve_tags_normalizes_tag_names(db_session: AsyncSession) -> None:
    """resolve_tags normalizes tag names (lowercase, trim)."""
    from app.services.tag_service import TagService

    service = TagService(db_session)
    tags = await service.resolve_tags(["  Focus  ", "URGENT"])

    assert len(tags) == 2
    assert {t.name for t in tags} == {"focus", "urgent"}


async def test_resolve_tags_reuses_existing_tags(db_session: AsyncSession) -> None:
    """resolve_tags returns existing tags, creating only missing ones."""
    from app.services.tag_service import TagService

    service = TagService(db_session)

    # Create first tag
    tags1 = await service.resolve_tags(["focus"])
    await db_session.commit()

    # Resolve with both existing and new
    tags2 = await service.resolve_tags(["focus", "urgent"])
    await db_session.commit()

    assert len(tags2) == 2
    assert tags2[0].name == "focus"
    assert tags2[1].name == "urgent"

    # Verify no duplicate "focus" tag was created
    result = await db_session.execute(select(Tag))
    all_tags = list(result.scalars().all())
    assert len(all_tags) == 2


async def test_resolve_tags_enforces_max_tags_limit(db_session: AsyncSession) -> None:
    """resolve_tags raises InvalidOperationError when tag count exceeds MAX_TAGS_PER_TASK."""
    from app.exceptions import InvalidOperationError
    from app.services.tag_service import TagService

    service = TagService(db_session)
    tag_names = [f"tag{i}" for i in range(6)]  # MAX_TAGS_PER_TASK is 5

    with pytest.raises(InvalidOperationError) as exc_info:
        await service.resolve_tags(tag_names)

    assert "tag" in str(exc_info.value).lower() or "max" in str(exc_info.value).lower()


async def test_resolve_tags_raises_invalid_operation_error(db_session: AsyncSession) -> None:
    """resolve_tags raises InvalidOperationError (not HTTPException) when over the tag limit."""
    from app.exceptions import InvalidOperationError
    from app.services.tag_service import TagService

    service = TagService(db_session)
    tag_names = [f"tag{i}" for i in range(6)]  # MAX_TAGS_PER_TASK is 5

    with pytest.raises(InvalidOperationError):
        await service.resolve_tags(tag_names)
