"""Shared constants for task categories, statuses, and limits."""

# Task categories (3-3-3 Technique)
CATEGORY_DEEP_WORK = "deep_work"
CATEGORY_SHORT_TASK = "short_task"
CATEGORY_MAINTENANCE = "maintenance"
VALID_CATEGORIES = {CATEGORY_DEEP_WORK, CATEGORY_SHORT_TASK, CATEGORY_MAINTENANCE}

# Task lifecycle statuses
STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_ROLLED_FORWARD = "rolled_forward"  # internal-only; not in VALID_STATUSES
VALID_STATUSES = {STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETED}

# Goal statuses
STATUS_GOAL_ACTIVE = "active"
STATUS_GOAL_COMPLETED = "completed"

# Settings keys (stored in Setting model)
RECURRING_DAYS_OFF_KEY = "recurring_days_off"
TIMER_DISPLAY_KEY = "timer_display"
FOCUS_GOAL_KEY = "focus_goal_id"

# Valid weekday names for settings
VALID_WEEKDAYS = frozenset(
    {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
)

# Deep work goal — 3 hours in seconds
DEEP_WORK_GOAL_SECONDS = 10800

# Business rules
MAX_TAGS_PER_TASK = 5
