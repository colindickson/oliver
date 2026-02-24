"""Shared package for Oliver backend and MCP server."""

from oliver_shared.constants import (
    CATEGORY_DEEP_WORK,
    CATEGORY_MAINTENANCE,
    CATEGORY_SHORT_TASK,
    MAX_TAGS_PER_TASK,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    VALID_CATEGORIES,
    VALID_STATUSES,
)
from oliver_shared.validation import normalize_tag_name, validate_tag_count

__all__ = [
    "CATEGORY_DEEP_WORK",
    "CATEGORY_MAINTENANCE",
    "CATEGORY_SHORT_TASK",
    "MAX_TAGS_PER_TASK",
    "STATUS_COMPLETED",
    "STATUS_IN_PROGRESS",
    "STATUS_PENDING",
    "VALID_CATEGORIES",
    "VALID_STATUSES",
    "normalize_tag_name",
    "validate_tag_count",
]
