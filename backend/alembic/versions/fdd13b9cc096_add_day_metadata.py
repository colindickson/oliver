"""add_day_metadata

Revision ID: fdd13b9cc096
Revises: dc68ad4bbc2b
Create Date: 2026-02-25 15:54:14.164676

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fdd13b9cc096'
down_revision: Union[str, None] = 'dc68ad4bbc2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'day_metadata',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('day_id', sa.Integer(), nullable=False),
        sa.Column('temperature_c', sa.Float(), nullable=True),
        sa.Column('condition', sa.String(length=50), nullable=True),
        sa.Column('moon_phase', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['day_id'], ['days.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('day_id'),
    )


def downgrade() -> None:
    op.drop_table('day_metadata')
