"""add daily_notes roadblocks day_ratings tables

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-02-23 00:00:00.000000

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: str = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "daily_notes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "day_id",
            sa.Integer(),
            sa.ForeignKey("days.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_daily_notes_day_id", "daily_notes", ["day_id"], unique=True)

    op.create_table(
        "roadblocks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "day_id",
            sa.Integer(),
            sa.ForeignKey("days.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_roadblocks_day_id", "roadblocks", ["day_id"], unique=True)

    op.create_table(
        "day_ratings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "day_id",
            sa.Integer(),
            sa.ForeignKey("days.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("focus", sa.Integer(), nullable=True),
        sa.Column("energy", sa.Integer(), nullable=True),
        sa.Column("satisfaction", sa.Integer(), nullable=True),
    )
    op.create_index("ix_day_ratings_day_id", "day_ratings", ["day_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_day_ratings_day_id", table_name="day_ratings")
    op.drop_table("day_ratings")

    op.drop_index("ix_roadblocks_day_id", table_name="roadblocks")
    op.drop_table("roadblocks")

    op.drop_index("ix_daily_notes_day_id", table_name="daily_notes")
    op.drop_table("daily_notes")
