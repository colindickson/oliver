"""add_template_schedules

Revision ID: 2ba492a38cff
Revises: 8108a2a45bc3
Create Date: 2026-02-28 00:37:11.298137

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ba492a38cff'
down_revision: Union[str, None] = '8108a2a45bc3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('template_schedules',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('template_id', sa.Integer(), nullable=False),
    sa.Column('recurrence', sa.String(length=20), nullable=False),
    sa.Column('anchor_date', sa.Date(), nullable=False),
    sa.Column('next_run_date', sa.Date(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['template_id'], ['task_templates.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_template_schedules_next_run_date'), 'template_schedules', ['next_run_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_template_schedules_next_run_date'), table_name='template_schedules')
    op.drop_table('template_schedules')
