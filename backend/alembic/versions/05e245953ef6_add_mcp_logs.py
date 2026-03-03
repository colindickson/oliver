"""add mcp logs

Revision ID: 05e245953ef6
Revises: b5e44acfc9a9
Create Date: 2026-03-03 10:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "05e245953ef6"
down_revision: Union[str, None] = "b5e44acfc9a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mcp_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("params", sa.Text(), nullable=False),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("before_state", sa.Text(), nullable=True),
        sa.Column(
            "is_reverted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_mcp_logs_created_at", "mcp_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_mcp_logs_created_at", table_name="mcp_logs")
    op.drop_table("mcp_logs")
