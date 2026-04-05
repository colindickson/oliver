"""add constraints and indexes

Revision ID: 847ac691d267
Revises: af8fbba5b772
Create Date: 2026-04-05 17:17:59.758003

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '847ac691d267'
down_revision: Union[str, None] = 'af8fbba5b772'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New indexes for frequently queried columns
    op.create_index('ix_task_tags_tag_id', 'task_tags', ['tag_id'], unique=False)
    op.create_index('ix_tasks_day_id_category', 'tasks', ['day_id', 'category'], unique=False)
    op.create_index('ix_goal_tags_tag_id', 'goal_tags', ['tag_id'], unique=False)
    op.create_index('ix_goal_tasks_task_id', 'goal_tasks', ['task_id'], unique=False)
    op.create_index('ix_notifications_created_at', 'notifications', [sa.text('created_at DESC')], unique=False)
    op.create_index('ix_reminders_delivered_remind_at', 'reminders', ['is_delivered', 'remind_at'], unique=False)

    # Replace mcp_logs created_at index with DESC version
    op.drop_index('ix_mcp_logs_created_at', table_name='mcp_logs')
    op.create_index('ix_mcp_logs_created_at', 'mcp_logs', [sa.text('created_at DESC')], unique=False)

    # CHECK constraints for data integrity
    op.create_check_constraint(
        'ck_timer_sessions_duration_nonneg',
        'timer_sessions',
        sa.or_(
            sa.column('duration_seconds').is_(None),
            sa.column('duration_seconds') >= 0,
        ),
    )
    op.create_check_constraint(
        'ck_timer_sessions_ended_after_started',
        'timer_sessions',
        sa.or_(
            sa.column('ended_at').is_(None),
            sa.column('ended_at') >= sa.column('started_at'),
        ),
    )
    op.create_check_constraint(
        'ck_tasks_category_valid',
        'tasks',
        sa.or_(
            sa.column('category').is_(None),
            sa.column('category').in_(['deep_work', 'short_task', 'maintenance']),
        ),
    )
    op.create_check_constraint(
        'ck_tasks_order_index_nonneg',
        'tasks',
        sa.column('order_index') >= 0,
    )

    # Add explicit length to title column (was unbounded String)
    op.alter_column('tasks', 'title',
                    existing_type=sa.String(),
                    type_=sa.String(255),
                    existing_nullable=False)


def downgrade() -> None:
    # Revert title column
    op.alter_column('tasks', 'title',
                    existing_type=sa.String(255),
                    type_=sa.String(),
                    existing_nullable=False)

    # Drop CHECK constraints
    op.drop_constraint('ck_tasks_order_index_nonneg', 'tasks', type_='check')
    op.drop_constraint('ck_tasks_category_valid', 'tasks', type_='check')
    op.drop_constraint('ck_timer_sessions_ended_after_started', 'timer_sessions', type_='check')
    op.drop_constraint('ck_timer_sessions_duration_nonneg', 'timer_sessions', type_='check')

    # Revert mcp_logs index
    op.drop_index('ix_mcp_logs_created_at', table_name='mcp_logs')
    op.create_index('ix_mcp_logs_created_at', 'mcp_logs', ['created_at'], unique=False)

    # Drop new indexes
    op.drop_index('ix_reminders_delivered_remind_at', table_name='reminders')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_goal_tasks_task_id', table_name='goal_tasks')
    op.drop_index('ix_goal_tags_tag_id', table_name='goal_tags')
    op.drop_index('ix_tasks_day_id_category', table_name='tasks')
    op.drop_index('ix_task_tags_tag_id', table_name='task_tags')
