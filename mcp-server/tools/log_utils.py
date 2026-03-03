"""Utility for writing MCP tool-call audit log entries."""

import json
from datetime import datetime, timedelta, timezone

from db import SessionLocal
from models.mcp_log import MCPLog

_RETENTION_DAYS = 7
_MAX_ENTRIES = 500


def log_call(
    tool_name: str,
    params: dict,
    result: str | None,
    status: str,
    before_state: dict | None = None,
) -> None:
    """Write a log entry for an MCP tool call and prune stale entries.

    Opens its own DB session so callers don't need to coordinate transactions.

    Args:
        tool_name: Name of the MCP tool that was called.
        params: Dict of parameters passed to the tool.
        result: JSON-encoded result string, or None if the call errored before producing one.
        status: ``'success'`` or ``'error'``.
        before_state: Dict snapshot of relevant state before the mutation, or None for reads.
    """
    with SessionLocal() as session:
        entry = MCPLog(
            tool_name=tool_name,
            params=json.dumps(params),
            result=result,
            status=status,
            before_state=json.dumps(before_state) if before_state is not None else None,
        )
        session.add(entry)
        session.flush()
        _prune(session)
        session.commit()


def _prune(session) -> None:
    """Remove entries older than 7 days and keep only the newest 500."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=_RETENTION_DAYS)
    session.query(MCPLog).filter(MCPLog.created_at < cutoff).delete(
        synchronize_session=False
    )
    subq = (
        session.query(MCPLog.id)
        .order_by(MCPLog.created_at.desc())
        .offset(_MAX_ENTRIES)
        .subquery()
    )
    session.query(MCPLog).filter(MCPLog.id.in_(subq)).delete(
        synchronize_session=False
    )
