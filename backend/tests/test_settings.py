"""Tests for the settings API endpoints.

Covers:
- GET /api/settings/timer-display (default true)
- PUT /api/settings/timer-display (save false)
- PUT /api/settings/timer-display (save true)
- GET after PUT reflects stored value
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Day  # ensure all tables are registered


async def test_get_timer_display_default(client: AsyncClient) -> None:
    """GET timer-display returns enabled=true when no setting has been stored."""
    response = await client.get("/api/settings/timer-display")
    assert response.status_code == 200
    assert response.json() == {"enabled": True}


async def test_put_timer_display_false(client: AsyncClient) -> None:
    """PUT timer-display with enabled=false saves and returns false."""
    response = await client.put("/api/settings/timer-display", json={"enabled": False})
    assert response.status_code == 200
    assert response.json() == {"enabled": False}


async def test_put_timer_display_true(client: AsyncClient) -> None:
    """PUT timer-display with enabled=true saves and returns true."""
    response = await client.put("/api/settings/timer-display", json={"enabled": True})
    assert response.status_code == 200
    assert response.json() == {"enabled": True}


async def test_get_timer_display_reflects_stored_value(client: AsyncClient) -> None:
    """GET timer-display after PUT returns the last stored value."""
    await client.put("/api/settings/timer-display", json={"enabled": False})
    response = await client.get("/api/settings/timer-display")
    assert response.status_code == 200
    assert response.json() == {"enabled": False}

    await client.put("/api/settings/timer-display", json={"enabled": True})
    response = await client.get("/api/settings/timer-display")
    assert response.status_code == 200
    assert response.json() == {"enabled": True}
