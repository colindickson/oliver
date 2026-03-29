"""add version column to settings

Revision ID: af8fbba5b772
Revises: d7e8f9a0b1c2
Create Date: 2026-03-28 14:36:26.503638

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af8fbba5b772'
down_revision: Union[str, None] = 'd7e8f9a0b1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('settings', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    op.drop_column('settings', 'version')
