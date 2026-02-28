"""Integration tests for the /api/templates endpoints."""

from __future__ import annotations

from datetime import date, date as _date, datetime, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.models import Day, Task  # noqa: F401 — register all tables
from app.models.task_template import TaskTemplate  # noqa: F401
from app.services.template_service import compute_next_run

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
    """Insert a Day record for instantiate tests."""
    d = Day(date=date(2025, 6, 1), created_at=datetime.now(timezone.utc))
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


# ---------------------------------------------------------------------------
# POST /api/templates
# ---------------------------------------------------------------------------


async def test_create_template_minimal(client: AsyncClient) -> None:
    """POST /api/templates creates a template with just a title."""
    response = await client.post("/api/templates", json={"title": "Daily standup"})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Daily standup"
    assert body["description"] is None
    assert body["category"] is None
    assert body["tags"] == []
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


async def test_create_template_full(client: AsyncClient) -> None:
    """POST /api/templates creates a template with all fields."""
    response = await client.post("/api/templates", json={
        "title": "Deep focus session",
        "description": "2-hour uninterrupted work block",
        "category": "deep_work",
        "tags": ["focus", "writing"],
    })

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Deep focus session"
    assert body["description"] == "2-hour uninterrupted work block"
    assert body["category"] == "deep_work"
    assert set(body["tags"]) == {"focus", "writing"}


# ---------------------------------------------------------------------------
# GET /api/templates
# ---------------------------------------------------------------------------


async def test_list_templates_empty(client: AsyncClient) -> None:
    """GET /api/templates returns an empty list when none exist."""
    response = await client.get("/api/templates")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_templates_returns_all(client: AsyncClient) -> None:
    """GET /api/templates returns all templates sorted by title."""
    await client.post("/api/templates", json={"title": "Zeta task"})
    await client.post("/api/templates", json={"title": "Alpha task"})

    response = await client.get("/api/templates")

    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Alpha task", "Zeta task"]


async def test_list_templates_search(client: AsyncClient) -> None:
    """GET /api/templates?search= filters by title substring."""
    await client.post("/api/templates", json={"title": "Morning review"})
    await client.post("/api/templates", json={"title": "Evening standup"})

    response = await client.get("/api/templates?search=morning")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Morning review"


# ---------------------------------------------------------------------------
# GET /api/templates/{id}
# ---------------------------------------------------------------------------


async def test_get_template(client: AsyncClient) -> None:
    """GET /api/templates/{id} returns the template."""
    created = (await client.post("/api/templates", json={"title": "My template"})).json()

    response = await client.get(f"/api/templates/{created['id']}")

    assert response.status_code == 200
    assert response.json()["title"] == "My template"


async def test_get_template_not_found(client: AsyncClient) -> None:
    """GET /api/templates/9999 returns 404."""
    response = await client.get("/api/templates/9999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/templates/{id}
# ---------------------------------------------------------------------------


async def test_update_template_title(client: AsyncClient) -> None:
    """PUT /api/templates/{id} updates specified fields."""
    created = (await client.post("/api/templates", json={"title": "Old title"})).json()

    response = await client.put(
        f"/api/templates/{created['id']}",
        json={"title": "New title"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "New title"


async def test_update_template_tags(client: AsyncClient) -> None:
    """PUT /api/templates/{id} replaces tags when provided."""
    created = (await client.post("/api/templates", json={
        "title": "Tagged template",
        "tags": ["old-tag"],
    })).json()

    response = await client.put(
        f"/api/templates/{created['id']}",
        json={"tags": ["new-tag1", "new-tag2"]},
    )

    assert response.status_code == 200
    assert set(response.json()["tags"]) == {"new-tag1", "new-tag2"}


async def test_update_template_not_found(client: AsyncClient) -> None:
    """PUT /api/templates/9999 returns 404."""
    response = await client.put("/api/templates/9999", json={"title": "X"})

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/templates/{id}
# ---------------------------------------------------------------------------


async def test_delete_template(client: AsyncClient) -> None:
    """DELETE /api/templates/{id} removes the template."""
    created = (await client.post("/api/templates", json={"title": "To delete"})).json()

    delete_resp = await client.delete(f"/api/templates/{created['id']}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True

    get_resp = await client.get(f"/api/templates/{created['id']}")
    assert get_resp.status_code == 404


async def test_delete_template_not_found(client: AsyncClient) -> None:
    """DELETE /api/templates/9999 returns 404."""
    response = await client.delete("/api/templates/9999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/templates/{id}/instantiate
# ---------------------------------------------------------------------------


async def test_instantiate_template_with_category_from_template(
    client: AsyncClient, day: Day
) -> None:
    """POST instantiate creates a task using the template's category."""
    created = (await client.post("/api/templates", json={
        "title": "Review PRs",
        "description": "Check open pull requests",
        "category": "short_task",
        "tags": ["review"],
    })).json()

    response = await client.post(
        f"/api/templates/{created['id']}/instantiate",
        json={"day_id": day.id},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Review PRs"
    assert body["description"] == "Check open pull requests"
    assert body["category"] == "short_task"
    assert body["day_id"] == day.id
    assert body["status"] == "pending"
    assert "review" in body["tags"]


async def test_instantiate_template_with_category_override(
    client: AsyncClient, day: Day
) -> None:
    """POST instantiate uses category_override when provided."""
    created = (await client.post("/api/templates", json={
        "title": "Generic task",
        "category": "maintenance",
    })).json()

    response = await client.post(
        f"/api/templates/{created['id']}/instantiate",
        json={"day_id": day.id, "category": "deep_work"},
    )

    assert response.status_code == 200
    assert response.json()["category"] == "deep_work"


async def test_instantiate_template_no_category_returns_400(
    client: AsyncClient, day: Day
) -> None:
    """POST instantiate without category on template or payload returns 400."""
    created = (await client.post("/api/templates", json={"title": "No category"})).json()

    response = await client.post(
        f"/api/templates/{created['id']}/instantiate",
        json={"day_id": day.id},
    )

    assert response.status_code == 400


async def test_instantiate_template_not_found(client: AsyncClient, day: Day) -> None:
    """POST instantiate with non-existent template ID returns 404."""
    response = await client.post(
        "/api/templates/9999/instantiate",
        json={"day_id": day.id, "category": "short_task"},
    )

    assert response.status_code == 404


async def test_instantiate_places_task_at_end(client: AsyncClient, day: Day) -> None:
    """POST instantiate sets order_index to count of existing tasks in category."""
    template = (await client.post("/api/templates", json={
        "title": "Template",
        "category": "short_task",
    })).json()

    # Instantiate twice → second task gets order_index 1
    r1 = await client.post(f"/api/templates/{template['id']}/instantiate", json={"day_id": day.id})
    r2 = await client.post(f"/api/templates/{template['id']}/instantiate", json={"day_id": day.id})

    assert r1.json()["order_index"] == 0
    assert r2.json()["order_index"] == 1


# ---------------------------------------------------------------------------
# TemplateSchedule model existence
# ---------------------------------------------------------------------------

async def test_schedule_model_fields(db_session: AsyncSession) -> None:
    """TemplateSchedule can be created with required fields."""
    from app.models.task_template import TemplateSchedule
    from datetime import date

    template = TaskTemplate(title="Yoga")
    db_session.add(template)
    await db_session.flush()

    schedule = TemplateSchedule(
        template_id=template.id,
        recurrence="weekly",
        anchor_date=date(2026, 3, 3),
        next_run_date=date(2026, 3, 3),
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)

    assert schedule.id is not None
    assert schedule.recurrence == "weekly"
    assert schedule.anchor_date == date(2026, 3, 3)
    assert schedule.next_run_date == date(2026, 3, 3)


# ---------------------------------------------------------------------------
# compute_next_run utility
# ---------------------------------------------------------------------------


def test_compute_next_run_weekly():
    assert compute_next_run(_date(2026, 3, 2), "weekly") == _date(2026, 3, 9)


def test_compute_next_run_bi_weekly():
    assert compute_next_run(_date(2026, 3, 2), "bi_weekly") == _date(2026, 3, 16)


def test_compute_next_run_monthly():
    assert compute_next_run(_date(2026, 1, 31), "monthly") == _date(2026, 2, 28)


def test_compute_next_run_monthly_normal():
    assert compute_next_run(_date(2026, 3, 15), "monthly") == _date(2026, 4, 15)


def test_compute_next_run_monthly_no_drift():
    """Monthly schedule with anchor_day=31 should not drift after short months."""
    # Feb 28 (clamped from Jan 31) → should return Mar 31, not Mar 28
    assert compute_next_run(_date(2026, 2, 28), "monthly", anchor_day=31) == _date(2026, 3, 31)


# ---------------------------------------------------------------------------
# Schedule CRUD API endpoints
# ---------------------------------------------------------------------------


async def test_create_schedule(client: AsyncClient) -> None:
    """POST /api/templates/{id}/schedules creates a schedule."""
    template = (await client.post("/api/templates", json={"title": "Yoga"})).json()

    response = await client.post(
        f"/api/templates/{template['id']}/schedules",
        json={"recurrence": "weekly", "anchor_date": "2026-03-03"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["recurrence"] == "weekly"
    assert body["anchor_date"] == "2026-03-03"
    assert body["next_run_date"] == "2026-03-03"
    assert body["template_id"] == template["id"]
    assert "id" in body


async def test_create_schedule_invalid_recurrence(client: AsyncClient) -> None:
    """POST /api/templates/{id}/schedules with bad recurrence returns 422."""
    template = (await client.post("/api/templates", json={"title": "Yoga"})).json()

    response = await client.post(
        f"/api/templates/{template['id']}/schedules",
        json={"recurrence": "daily", "anchor_date": "2026-03-03"},
    )

    assert response.status_code == 422


async def test_list_schedules(client: AsyncClient) -> None:
    """GET /api/templates/{id}/schedules lists all schedules for a template."""
    template = (await client.post("/api/templates", json={"title": "Yoga"})).json()
    await client.post(
        f"/api/templates/{template['id']}/schedules",
        json={"recurrence": "weekly", "anchor_date": "2026-03-03"},
    )
    await client.post(
        f"/api/templates/{template['id']}/schedules",
        json={"recurrence": "monthly", "anchor_date": "2026-03-03"},
    )

    response = await client.get(f"/api/templates/{template['id']}/schedules")

    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_schedules_empty(client: AsyncClient) -> None:
    """GET /api/templates/{id}/schedules returns [] when none exist."""
    template = (await client.post("/api/templates", json={"title": "Empty"})).json()

    response = await client.get(f"/api/templates/{template['id']}/schedules")

    assert response.status_code == 200
    assert response.json() == []


async def test_delete_schedule(client: AsyncClient) -> None:
    """DELETE /api/templates/{id}/schedules/{sid} removes the schedule."""
    template = (await client.post("/api/templates", json={"title": "Yoga"})).json()
    schedule = (await client.post(
        f"/api/templates/{template['id']}/schedules",
        json={"recurrence": "weekly", "anchor_date": "2026-03-03"},
    )).json()

    del_resp = await client.delete(
        f"/api/templates/{template['id']}/schedules/{schedule['id']}"
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

    list_resp = await client.get(f"/api/templates/{template['id']}/schedules")
    assert list_resp.json() == []


async def test_delete_schedule_not_found(client: AsyncClient) -> None:
    """DELETE /api/templates/1/schedules/9999 returns 404."""
    template = (await client.post("/api/templates", json={"title": "Yoga"})).json()

    response = await client.delete(
        f"/api/templates/{template['id']}/schedules/9999"
    )
    assert response.status_code == 404
