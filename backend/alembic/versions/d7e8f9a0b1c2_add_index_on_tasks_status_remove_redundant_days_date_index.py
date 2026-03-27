"""add index on tasks.status, remove redundant days.date index

Revision ID: d7e8f9a0b1c2
Revises: a3b4c5d6e7f8
Create Date: 2026-03-27 22:13:49.473604

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd7e8f9a0b1c2'
down_revision: Union[str, None] = 'a3b4c5d6e7f8'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.drop_index('ix_days_date', table_name='days')


def downgrade() -> None:
    op.create_index('ix_days_date', 'days', ['date'])
    op.drop_index('ix_tasks_status', table_name='tasks')
