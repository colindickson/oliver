"""add_log_type_to_work_logs

Revision ID: e1f2a3b4c5d6
Revises: fdd13b9cc096
Create Date: 2026-04-28 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "6893952f5742"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    log_type_enum = sa.Enum("commit", "pr", "review", "research", name="log_type")
    log_type_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "work_logs",
        sa.Column("log_type", log_type_enum, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("work_logs", "log_type")
    sa.Enum(name="log_type").drop(op.get_bind(), checkfirst=True)
