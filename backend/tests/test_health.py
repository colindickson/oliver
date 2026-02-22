"""Tests for the health check endpoint.

Written before the endpoint exists (TDD red phase).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_health_check() -> None:
    """GET /api/health returns 200 and {"status": "ok"}."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
