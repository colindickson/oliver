"""Individual task CRUD tools."""

import json
from datetime import date, datetime, timezone

from sqlalchemy import and_, case, exists, or_
from sqlalchemy.orm import aliased

from models.day import Day
from models.tag import Tag
from models.task import Task
from tools.daily import get_session, _get_or_create_day
from tools.log_utils import log_call
from oliver_shared import (
    MAX_TAGS_PER_TASK,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    VALID_STATUSES,
    normalize_tag_name,
    validate_tag_count,
)


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
        normalized = normalize_tag_name(name)
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
    params = {"title": title, "category": category, "day_date": day_date,
              "description": description, "tags": tags}
    try:
        validate_tag_count(tags)
    except ValueError as e:
        error_json = json.dumps({"error": str(e)})
        log_call("create_task", params, error_json, "error")
        return error_json

    target = date.fromisoformat(day_date) if day_date else date.today()
    try:
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
        result_json = json.dumps(result)
        log_call("create_task", params, result_json, "success", before_state=None)
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("create_task", params, error_json, "error")
        return error_json


def update_task(
    task_id: int,
    title: str = "",
    description: str = "",
    status: str = "",
    tags: list[str] | None = None,
) -> str:
    """Update one or more fields on an existing task.

    Only fields with non-empty values are applied; omitted fields are left
    unchanged. Setting *status* to ``completed`` also records ``completed_at``.

    Args:
        task_id: Primary key of the task to update.
        title: New title, or empty string to leave unchanged.
        description: New description, or empty string to leave unchanged.
        status: New status value, or empty string to leave unchanged.
        tags: None to leave unchanged, [] to clear all tags, list to replace (max 5).

    Returns:
        JSON-encoded dict with ``success``, ``task_id``, and ``tags``, or an ``error``
        key when the task is not found.
    """
    params = {"task_id": task_id, "title": title, "description": description,
              "status": status, "tags": tags}
    if status and status not in VALID_STATUSES:
        valid = ", ".join(sorted(VALID_STATUSES))
        error_json = json.dumps({"error": f"Invalid status '{status}'. Valid values: {valid}"})
        log_call("update_task", params, error_json, "error")
        return error_json
    try:
        with get_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if not task:
                error_json = json.dumps({"error": f"Task {task_id} not found"})
                log_call("update_task", params, error_json, "error")
                return error_json

            before_state = {
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "category": task.category,
                "tags": [t.name for t in task.tags],
            }

            if title:
                task.title = title
            if description:
                task.description = description
            if status:
                task.status = status
                if status == STATUS_COMPLETED:
                    task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

            if tags is not None:
                try:
                    validate_tag_count(tags)
                except ValueError as e:
                    error_json = json.dumps({"error": str(e)})
                    log_call("update_task", params, error_json, "error")
                    return error_json
                tag_objects = _get_or_create_tags(session, tags)
                task.tags = tag_objects

            final_tags = [t.name for t in task.tags]

        result_json = json.dumps({"success": True, "task_id": task_id, "tags": final_tags})
        log_call("update_task", params, result_json, "success", before_state=before_state)
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("update_task", params, error_json, "error")
        return error_json


def delete_task(task_id: int) -> str:
    """Permanently delete a task by ID.

    Args:
        task_id: Primary key of the task to delete.

    Returns:
        JSON-encoded dict with ``deleted`` and ``task_id``, or an ``error``
        key when the task is not found.
    """
    params = {"task_id": task_id}
    try:
        with get_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if not task:
                error_json = json.dumps({"error": f"Task {task_id} not found"})
                log_call("delete_task", params, error_json, "error")
                return error_json

            day = task.day
            before_state = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "category": task.category,
                "day_date": day.date.isoformat() if day else None,
                "tags": [t.name for t in task.tags],
            }
            session.delete(task)

        result_json = json.dumps({"deleted": True, "task_id": task_id})
        log_call("delete_task", params, result_json, "success", before_state=before_state)
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("delete_task", params, error_json, "error")
        return error_json


def add_backlog_task(
    title: str,
    description: str = "",
    tags: list[str] | None = None,
) -> str:
    """Add a task to the backlog (no day assigned, no category).

    Returns:
        JSON-encoded dict with created task or error.
    """
    if tags is None:
        tags = []

    params = {"title": title, "description": description, "tags": tags}

    try:
        validate_tag_count(tags)
    except ValueError as e:
        error_json = json.dumps({"error": str(e)})
        log_call("add_backlog_task", params, error_json, "error")
        return error_json

    try:
        with get_session() as session:
            existing_count = session.query(Task).filter(Task.day_id.is_(None)).count()
            task = Task(
                day_id=None,
                category=None,
                title=title,
                description=description or None,
                order_index=existing_count,
            )
            session.add(task)
            session.flush()

            if tags:
                task.tags = _get_or_create_tags(session, tags)

            result = {
                "id": task.id,
                "title": task.title,
                "category": task.category,
                "status": task.status,
                "tags": [t.name for t in task.tags],
                "day_id": task.day_id,
            }

        result_json = json.dumps(result)
        log_call("add_backlog_task", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("add_backlog_task", params, error_json, "error")
        return error_json


def list_backlog(tag: str = "", search: str = "", include_completed: bool = False) -> str:
    """List idle tasks: pending/in-progress work with no day, or on any day but today.

    Mirrors GET /api/backlog (same predicate, hand-copied) minus tasks that
    already have a continuation. Ordered: no day (by ``order_index``), past
    days most-recent-first, then future days soonest-first.

    Args:
        tag: Only tasks carrying this tag (normalized like stored tags).
        search: Case-insensitive substring match on title (wildcards are literal).
        include_completed: Also list completed tasks with no day (anything but
            rolled_forward), so callers that dedupe by tag still see them.

    Returns:
        JSON list of dicts with ``id``, ``title``, ``description``, ``status``,
        ``tags`` and ``day`` (ISO date or None), or an ``error`` dict on failure.
    """
    params = {"tag": tag, "search": search, "include_completed": include_completed}
    try:
        with get_session() as session:
            today = date.today()
            continuation = aliased(Task)
            idle = and_(
                Task.status.in_((STATUS_PENDING, STATUS_IN_PROGRESS)),
                or_(Task.day_id.is_(None), Day.date != today),
                ~exists().where(continuation.rolled_from_task_id == Task.id),
            )
            if include_completed:
                # Idle tasks plus completed day-less ones, never all of history.
                idle = or_(
                    idle,
                    and_(Task.day_id.is_(None), Task.status == STATUS_COMPLETED),
                )
            query = (
                session.query(Task, Day.date)
                .outerjoin(Day, Task.day_id == Day.id)
                .filter(idle)
            )
            normalized = normalize_tag_name(tag) if tag else ""
            if normalized:
                query = query.filter(Task.tags.any(Tag.name == normalized))
            if search:
                escaped = (
                    search.replace("\\", "\\\\")
                    .replace("%", "\\%")
                    .replace("_", "\\_")
                )
                query = query.filter(Task.title.ilike(f"%{escaped}%", escape="\\"))
            result = [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "tags": [tg.name for tg in t.tags],
                    "day": d.isoformat() if d else None,
                }
                for t, d in query.order_by(
                    Task.day_id.isnot(None),
                    (Day.date > today).asc(),
                    case((Day.date > today, Day.date)).asc(),
                    case((Day.date < today, Day.date)).desc(),
                    Task.order_index,
                    Task.id,
                ).all()
            ]
        result_json = json.dumps(result)
        log_call("list_backlog", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("list_backlog", params, error_json, "error")
        return error_json


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
    params = {"task_id": task_id}
    try:
        with get_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if not task:
                error_json = json.dumps({"error": f"Task {task_id} not found"})
                log_call("complete_task", params, error_json, "error")
                return error_json

            before_state = {
                "status": task.status,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            }

            task.status = STATUS_COMPLETED
            task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        result_json = json.dumps({"success": True, "task_id": task_id})
        log_call("complete_task", params, result_json, "success", before_state=before_state)
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("complete_task", params, error_json, "error")
        return error_json
