"""MCPLog model — audit log entry for every MCP tool call."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MCPLog(Base):
    """A single MCP tool-call log entry.

    Attributes:
        id: Auto-increment primary key.
        tool_name: Name of the MCP tool that was called.
        params: JSON-encoded parameters passed to the tool.
        result: JSON-encoded result returned by the tool (null on error before result).
        status: ``'success'`` or ``'error'``.
        before_state: JSON snapshot of relevant DB state before mutation (null for reads).
        is_reverted: True once the call has been successfully reverted.
        created_at: UTC timestamp when the log entry was created.
    """

    __tablename__ = "mcp_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    params: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    before_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_reverted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (Index("ix_mcp_logs_created_at", created_at.desc()),)
