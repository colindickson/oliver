"""add parent_goal_id to goals

Revision ID: 9e4799353a2b
Revises: cc4d1e2f3a5b
Create Date: 2026-06-09 15:48:38.631161

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e4799353a2b'
down_revision: Union[str, None] = 'cc4d1e2f3a5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('goals', sa.Column('parent_goal_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_goals_parent_goal_id'), 'goals', ['parent_goal_id'], unique=False)
    op.create_foreign_key(
        "fk_goals_parent_goal_id", "goals", "goals", ["parent_goal_id"], ["id"], ondelete="CASCADE"
    )


def downgrade() -> None:
    op.drop_constraint("fk_goals_parent_goal_id", "goals", type_="foreignkey")
    op.drop_index("ix_goals_parent_goal_id", table_name="goals")
    op.drop_column("goals", "parent_goal_id")
