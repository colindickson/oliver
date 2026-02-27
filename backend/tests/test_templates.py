"""Integration tests for the /api/templates endpoints."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.models import Day, Task  # noqa: F401 — register all tables
from app.models.task_template import TaskTemplate  # noqa: F401

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
