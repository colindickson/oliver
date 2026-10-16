"""Tests for the settings API endpoints.

Covers:
- GET/PUT /api/settings/focus-goal
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Day  # ensure all tables are registered


# ---------------------------------------------------------------------------
# GET /api/settings/focus-goal
# ---------------------------------------------------------------------------


async def test_get_focus_goal_default(client: AsyncClient) -> None:
    """GET focus-goal returns goal_id=null when no setting has been stored."""
    response = await client.get("/api/settings/focus-goal")
    assert response.status_code == 200
    assert response.json() == {"goal_id": None}


async def test_put_focus_goal_sets_value(client: AsyncClient) -> None:
    """PUT focus-goal with a goal_id saves and returns the value."""
    # Create a goal first so the ID is valid
    goal_resp = await client.post("/api/goals", json={"title": "Focus target"})
    goal_id = goal_resp.json()["id"]

    response = await client.put("/api/settings/focus-goal", json={"goal_id": goal_id})
    assert response.status_code == 200
    assert response.json() == {"goal_id": goal_id}


async def test_put_focus_goal_clears_value(client: AsyncClient) -> None:
    """PUT focus-goal with goal_id=null clears the setting."""
    # Set a value first
    goal_resp = await client.post("/api/goals", json={"title": "Temporary goal"})
    goal_id = goal_resp.json()["id"]
    await client.put("/api/settings/focus-goal", json={"goal_id": goal_id})

    # Clear it
    response = await client.put("/api/settings/focus-goal", json={"goal_id": None})
    assert response.status_code == 200
    assert response.json() == {"goal_id": None}


async def test_get_focus_goal_reflects_stored_value(client: AsyncClient) -> None:
    """GET focus-goal after PUT returns the last stored value."""
    goal_resp = await client.post("/api/goals", json={"title": "Stored goal"})
    goal_id = goal_resp.json()["id"]

    await client.put("/api/settings/focus-goal", json={"goal_id": goal_id})
    response = await client.get("/api/settings/focus-goal")
    assert response.status_code == 200
    assert response.json() == {"goal_id": goal_id}
