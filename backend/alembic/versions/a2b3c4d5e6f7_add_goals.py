"""add_goals

Revision ID: a2b3c4d5e6f7
Revises: fdd13b9cc096
Create Date: 2026-02-26 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'fdd13b9cc096'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'goals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'goal_tags',
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('goal_id', 'tag_id'),
    )
    op.create_table(
        'goal_tasks',
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('goal_id', 'task_id'),
    )


def downgrade() -> None:
    op.drop_table('goal_tasks')
    op.drop_table('goal_tags')
    op.drop_table('goals')
