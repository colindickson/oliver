"""Individual task CRUD tools."""

import json
from datetime import date, datetime, timezone

from models.tag import Tag
from models.task import Task, STATUS_COMPLETED
from tools.daily import get_session, _get_or_create_day

MAX_TAGS_PER_TASK = 5


def _get_or_create_tags(session, tag_names: list[str]) -> list[Tag]:
    """Return Tag objects for the given names, creating any that don't exist.

    Tags are normalized: stripped of whitespace and converted to lowercase.

    Args:
        session: An active SQLAlchemy session.
        tag_names: List of tag names to resolve.

    Returns:
        List of Tag objects.
    """
    tags = []
    for name in tag_names:
        normalized = name.strip().lower()
        if not normalized:
            continue
        tag = session.query(Tag).filter(Tag.name == normalized).first()
        if tag is None:
            tag = Tag(name=normalized)
            session.add(tag)
            session.flush()
        tags.append(tag)
    return tags


def create_task(
    title: str,
    category: str,
    day_date: str = "",
    description: str = "",
    tags: list[str] | None = None,
) -> str:
    """Create a new task and append it to the day's task list.

    The ``order_index`` is set to the current count of tasks in the same
    category, placing the new task at the end of its category group.

    Args:
        title: Short human-readable task title.
        category: One of ``deep_work``, ``short_task``, or ``maintenance``.
        day_date: ISO-8601 date string (YYYY-MM-DD). Defaults to today.
        description: Optional extended description.
        tags: Optional list of tag names (max 5, will be normalized).

    Returns:
        JSON-encoded dict with the created task's ``id``, ``title``,
        ``category``, ``status``, and ``tags``.
    """
    if tags is None:
        tags = []
    if len(tags) > MAX_TAGS_PER_TASK:
        return json.dumps({"error": f"Maximum {MAX_TAGS_PER_TASK} tags allowed per task"})

    target = date.fromisoformat(day_date) if day_date else date.today()
    with get_session() as session:
        day = _get_or_create_day(session, target)
        count = (
            session.query(Task)
            .filter(Task.day_id == day.id, Task.category == category)
            .count()
        )
        task = Task(
            day_id=day.id,
            category=category,
            title=title,
            description=description or None,
            order_index=count,
        )
        session.add(task)
        session.flush()

        # Add tags if provided
        if tags:
            tag_objects = _get_or_create_tags(session, tags)
            task.tags = tag_objects

        result = {
            "id": task.id,
            "title": task.title,
            "category": task.category,
            "status": task.status,
            "tags": [t.name for t in task.tags],
        }
    return json.dumps(result)


def update_task(
    task_id: int,
    title: str = "",
    description: str = "",
    status: str = "",
    tags: list[str] | str | None = None,
) -> str:
    """Update one or more fields on an existing task.

    Only fields with non-empty values are applied; omitted fields are left
    unchanged. Setting *status* to ``completed`` also records ``completed_at``.

    Args:
        task_id: Primary key of the task to update.
        title: New title, or empty string to leave unchanged.
        description: New description, or empty string to leave unchanged.
        status: New status value, or empty string to leave unchanged.
        tags: New tags - empty string means no change, empty list [] removes all tags,
              non-empty list replaces tags (max 5, will be normalized).

    Returns:
        JSON-encoded dict with ``success``, ``task_id``, and ``tags``, or an ``error``
        key when the task is not found.
    """
    with get_session() as session:
        task = session.query(Task).filter(Task.id == task_id).first()
        if not task:
            return json.dumps({"error": f"Task {task_id} not found"})
        if title:
            task.title = title
        if description:
            task.description = description
        if status:
            task.status = status
            if status == STATUS_COMPLETED:
                task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Handle tags - empty string means no change (backward compatible)
        if tags != "" and tags is not None:
            if isinstance(tags, str):
                tags = []
            if len(tags) > MAX_TAGS_PER_TASK:
                return json.dumps({"error": f"Maximum {MAX_TAGS_PER_TASK} tags allowed per task"})
            tag_objects = _get_or_create_tags(session, tags)
            task.tags = tag_objects

    result = {"success": True, "task_id": task_id, "tags": [t.name for t in task.tags]}
    return json.dumps(result)


def delete_task(task_id: int) -> str:
    """Permanently delete a task by ID.

    Args:
        task_id: Primary key of the task to delete.

    Returns:
        JSON-encoded dict with ``deleted`` and ``task_id``, or an ``error``
        key when the task is not found.
    """
    with get_session() as session:
        task = session.query(Task).filter(Task.id == task_id).first()
        if not task:
            return json.dumps({"error": f"Task {task_id} not found"})
        session.delete(task)
    return json.dumps({"deleted": True, "task_id": task_id})


def complete_task(task_id: int) -> str:
    """Mark a task as completed.

    Convenience wrapper around :func:`update_task` that sets status to
    ``completed`` and records the completion timestamp.

    Args:
        task_id: Primary key of the task to complete.

    Returns:
        JSON-encoded dict with ``success`` and ``task_id``, or an ``error``
        key when the task is not found.
    """
    return update_task(task_id, status=STATUS_COMPLETED)
