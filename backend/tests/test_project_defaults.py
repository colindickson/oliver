"""Tests for ProjectDefault API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models import ProjectDefault  # ensure table is registered


async def test_list_project_defaults_empty(client: AsyncClient) -> None:
    response = await client.get("/api/project-defaults")
    assert response.status_code == 200
    assert response.json() == []


async def test_upsert_creates_new(client: AsyncClient) -> None:
    response = await client.put(
        "/api/project-defaults/oliver",
        json={"default_tags": ["python", "backend"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "oliver"
    assert data["default_tags"] == ["python", "backend"]


async def test_upsert_replaces_existing(client: AsyncClient) -> None:
    await client.put("/api/project-defaults/oliver", json={"default_tags": ["a"]})
    response = await client.put("/api/project-defaults/oliver", json={"default_tags": ["b", "c"]})
    assert response.status_code == 200
    assert response.json()["default_tags"] == ["b", "c"]


async def test_get_project_default(client: AsyncClient) -> None:
    await client.put("/api/project-defaults/myproject", json={"default_tags": ["x"]})
    response = await client.get("/api/project-defaults/myproject")
    assert response.status_code == 200
    assert response.json()["default_tags"] == ["x"]


async def test_get_project_default_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/project-defaults/nonexistent")
    assert response.status_code == 404


async def test_upsert_too_many_tags(client: AsyncClient) -> None:
    response = await client.put(
        "/api/project-defaults/myproject",
        json={"default_tags": ["a", "b", "c", "d", "e", "f"]},
    )
    assert response.status_code == 400


async def test_list_returns_all_sorted(client: AsyncClient) -> None:
    await client.put("/api/project-defaults/zproject", json={"default_tags": []})
    await client.put("/api/project-defaults/aproject", json={"default_tags": []})
    response = await client.get("/api/project-defaults")
    assert response.status_code == 200
    names = [d["project_name"] for d in response.json()]
    assert names == sorted(names)
