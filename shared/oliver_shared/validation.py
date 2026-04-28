"""Shared validation functions for business rules."""

from oliver_shared.constants import MAX_TAGS_PER_TASK, VALID_LOG_TYPES


def normalize_tag_name(name: str) -> str:
    """Normalize a tag name by stripping whitespace and converting to lowercase.

    Args:
        name: The raw tag name input.

    Returns:
        The normalized tag name.
    """
    return name.strip().lower()


def validate_log_type(log_type: str | None) -> None:
    if log_type is not None and log_type not in VALID_LOG_TYPES:
        raise ValueError(
            f"Invalid log_type '{log_type}'. Must be one of: {', '.join(sorted(VALID_LOG_TYPES))}"
        )


def validate_tag_count(tags: list) -> None:
    """Validate that the number of tags does not exceed the maximum allowed.

    Args:
        tags: List of tags to validate.

    Raises:
        ValueError: If the number of tags exceeds MAX_TAGS_PER_TASK.
    """
    if len(tags) > MAX_TAGS_PER_TASK:
        raise ValueError(f"Maximum {MAX_TAGS_PER_TASK} tags allowed per task")
