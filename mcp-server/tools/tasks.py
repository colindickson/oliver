"""Individual task CRUD tools."""

import json
from datetime import date, datetime, timezone

from models.task import Task, STATUS_COMPLETED
from tools.daily import get_session, _get_or_create_day


def create_task(
    title: str,
    category: str,
    day_date: str = "",
    description: str = "",
) -> str:
    """Create a new task and append it to the day's task list.

    The ``order_index`` is set to the current count of tasks in the same
    category, placing the new task at the end of its category group.

    Args:
        title: Short human-readable task title.
        category: One of ``deep_work``, ``short_task``, or ``maintenance``.
        day_date: ISO-8601 date string (YYYY-MM-DD). Defaults to today.
        description: Optional extended description.

    Returns:
        JSON-encoded dict with the created task's ``id``, ``title``,
        ``category``, and ``status``.
    """
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
        result = {
            "id": task.id,
            "title": task.title,
            "category": task.category,
            "status": task.status,
        }
    return json.dumps(result)


def update_task(
    task_id: int,
    title: str = "",
    description: str = "",
    status: str = "",
) -> str:
    """Update one or more fields on an existing task.

    Only fields with non-empty values are applied; omitted fields are left
    unchanged. Setting *status* to ``completed`` also records ``completed_at``.

    Args:
        task_id: Primary key of the task to update.
        title: New title, or empty string to leave unchanged.
        description: New description, or empty string to leave unchanged.
        status: New status value, or empty string to leave unchanged.

    Returns:
        JSON-encoded dict with ``success`` and ``task_id``, or an ``error``
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
    return json.dumps({"success": True, "task_id": task_id})


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
