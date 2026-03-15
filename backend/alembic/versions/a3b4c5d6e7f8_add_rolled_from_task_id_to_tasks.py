"""add rolled_from_task_id to tasks

Revision ID: a3b4c5d6e7f8
Revises: 05e245953ef6
Create Date: 2026-03-15 10:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, None] = "05e245953ef6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("rolled_from_task_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_tasks_rolled_from_task_id",
        "tasks",
        "tasks",
        ["rolled_from_task_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_tasks_rolled_from_task_id", "tasks", type_="foreignkey")
    op.drop_column("tasks", "rolled_from_task_id")
