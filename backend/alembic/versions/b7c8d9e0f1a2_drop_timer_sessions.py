"""drop timer_sessions and timer settings

Revision ID: b7c8d9e0f1a2
Revises: 9e4799353a2b
Create Date: 2026-10-15 12:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = '9e4799353a2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_timer_sessions_task_id'), table_name='timer_sessions')
    op.drop_table('timer_sessions')
    op.execute("DELETE FROM settings WHERE key IN ('active_timer', 'timer_display')")


def downgrade() -> None:
    op.create_table('timer_sessions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('duration_seconds', sa.Integer(), nullable=True),
    sa.CheckConstraint('duration_seconds IS NULL OR duration_seconds >= 0', name='ck_timer_sessions_duration_nonneg'),
    sa.CheckConstraint('ended_at IS NULL OR ended_at >= started_at', name='ck_timer_sessions_ended_after_started'),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_timer_sessions_task_id'), 'timer_sessions', ['task_id'], unique=False)
