"""add external_source and external_id to tasks

Revision ID: c3d4e5f6a7b8
Revises: b7c8d9e0f1a2
Create Date: 2026-10-15 13:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('external_source', sa.String(length=50), nullable=True))
    op.add_column('tasks', sa.Column('external_id', sa.String(length=255), nullable=True))
    op.create_index('ix_tasks_external_ref', 'tasks', ['external_source', 'external_id'])


def downgrade() -> None:
    op.drop_index('ix_tasks_external_ref', table_name='tasks')
    op.drop_column('tasks', 'external_id')
    op.drop_column('tasks', 'external_source')
