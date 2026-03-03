"""Pydantic schemas for the MCP log resource."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

from app.services.mcp_log_service import REVERT_HANDLERS


class MCPLogResponse(BaseModel):
    """Response schema for a single MCP log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tool_name: str
    params: str
    result: str | None
    status: str
    is_reverted: bool
    created_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_revertible(self) -> bool:
        return (
            self.status == "success"
            and not self.is_reverted
            and self.tool_name in REVERT_HANDLERS
        )
