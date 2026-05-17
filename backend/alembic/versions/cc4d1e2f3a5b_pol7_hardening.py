"""POL-7 hardening: CHECK constraints, server_default, string lengths

Revision ID: cc4d1e2f3a5b
Revises: fa8bb402873f
Create Date: 2026-05-17 14:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'cc4d1e2f3a5b'
down_revision: str | None = 'fa8bb402873f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # goals.created_at: add server default
    op.alter_column('goals', 'created_at', server_default=sa.text('now()'))

    # day_ratings: enforce 1-5 range on nullable score columns
    op.create_check_constraint(
        'ck_day_ratings_focus_range',
        'day_ratings',
        'focus IS NULL OR (focus >= 1 AND focus <= 5)',
    )
    op.create_check_constraint(
        'ck_day_ratings_energy_range',
        'day_ratings',
        'energy IS NULL OR (energy >= 1 AND energy <= 5)',
    )
    op.create_check_constraint(
        'ck_day_ratings_satisfaction_range',
        'day_ratings',
        'satisfaction IS NULL OR (satisfaction >= 1 AND satisfaction <= 5)',
    )

    # String length caps (TEXT -> VARCHAR(n))
    op.alter_column('goals', 'title',
                    existing_type=sa.Text(),
                    type_=sa.String(500),
                    existing_nullable=False)
    op.alter_column('goals', 'description',
                    existing_type=sa.Text(),
                    type_=sa.String(10000),
                    existing_nullable=True)
    op.alter_column('tags', 'name',
                    existing_type=sa.Text(),
                    type_=sa.String(100),
                    existing_nullable=False)
    op.alter_column('settings', 'key',
                    existing_type=sa.Text(),
                    type_=sa.String(200),
                    existing_nullable=False)
    op.alter_column('settings', 'value',
                    existing_type=sa.Text(),
                    type_=sa.String(8192),
                    existing_nullable=False)
    op.alter_column('tasks', 'description',
                    existing_type=sa.Text(),
                    type_=sa.String(10000),
                    existing_nullable=True)
    op.alter_column('tasks', 'category',
                    existing_type=sa.Text(),
                    type_=sa.String(100),
                    existing_nullable=True)


def downgrade() -> None:
    op.drop_constraint('ck_day_ratings_satisfaction_range', 'day_ratings')
    op.drop_constraint('ck_day_ratings_energy_range', 'day_ratings')
    op.drop_constraint('ck_day_ratings_focus_range', 'day_ratings')

    op.alter_column('goals', 'created_at', server_default=None)

    op.alter_column('goals', 'title',
                    existing_type=sa.String(500),
                    type_=sa.Text(),
                    existing_nullable=False)
    op.alter_column('goals', 'description',
                    existing_type=sa.String(10000),
                    type_=sa.Text(),
                    existing_nullable=True)
    op.alter_column('tags', 'name',
                    existing_type=sa.String(100),
                    type_=sa.Text(),
                    existing_nullable=False)
    op.alter_column('settings', 'key',
                    existing_type=sa.String(200),
                    type_=sa.Text(),
                    existing_nullable=False)
    op.alter_column('settings', 'value',
                    existing_type=sa.String(8192),
                    type_=sa.Text(),
                    existing_nullable=False)
    op.alter_column('tasks', 'description',
                    existing_type=sa.String(10000),
                    type_=sa.Text(),
                    existing_nullable=True)
    op.alter_column('tasks', 'category',
                    existing_type=sa.String(100),
                    type_=sa.Text(),
                    existing_nullable=True)
