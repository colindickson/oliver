"""Shared constants for task categories, statuses, and limits."""

# Task categories (3-3-3 method)
CATEGORY_DEEP_WORK = "deep_work"
CATEGORY_SHORT_TASK = "short_task"
CATEGORY_MAINTENANCE = "maintenance"
VALID_CATEGORIES = {CATEGORY_DEEP_WORK, CATEGORY_SHORT_TASK, CATEGORY_MAINTENANCE}

# Task lifecycle statuses
STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
VALID_STATUSES = {STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETED}

# Business rules
MAX_TAGS_PER_TASK = 5
