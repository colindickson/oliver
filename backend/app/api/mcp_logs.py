"""FastAPI route handlers for the /api/mcp-logs resource."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.mcp_log import MCPLogResponse
from app.services.mcp_log_service import MCPLogService, REVERT_HANDLERS

router = APIRouter(prefix="/api/mcp-logs", tags=["mcp-logs"])


@router.get("", response_model=list[MCPLogResponse])
async def list_mcp_logs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[MCPLogResponse]:
    """Return MCP log entries ordered by created_at descending."""
    service = MCPLogService(db)
    logs = await service.list_logs(limit=limit, offset=offset)
    return [
        MCPLogResponse(
            id=log.id,
            tool_name=log.tool_name,
            params=log.params,
            result=log.result,
            status=log.status,
            is_reverted=log.is_reverted,
            is_revertible=(
                log.status == "success"
                and not log.is_reverted
                and log.tool_name in REVERT_HANDLERS
            ),
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.post("/{log_id}/revert", response_model=MCPLogResponse)
async def revert_mcp_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
) -> MCPLogResponse:
    """Revert the database mutation caused by the given log entry.

    Raises:
        HTTPException: 404 if the log entry does not exist.
        HTTPException: 422 if the entry is already reverted, failed, or has no handler.
    """
    service = MCPLogService(db)
    try:
        log = await service.revert(log_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return MCPLogResponse(
        id=log.id,
        tool_name=log.tool_name,
        params=log.params,
        result=log.result,
        status=log.status,
        is_reverted=log.is_reverted,
        is_revertible=False,  # just reverted, so no longer revertible
        created_at=log.created_at,
    )
