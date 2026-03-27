"""Pydantic schemas for the MCP log resource."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MCPLogResponse(BaseModel):
    """Response schema for a single MCP log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tool_name: str
    params: str
    result: str | None
    status: str
    is_reverted: bool
    is_revertible: bool = False
    created_at: datetime
