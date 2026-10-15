"""Goal tools: create, list and get goals."""

import json
from datetime import UTC, date, datetime

from oliver_shared import normalize_tag_name, validate_tag_count
from sqlalchemy import func, select

from models.goal import Goal
from models.tag import Tag, task_tags_table
from models.task import Task
from tools.daily import get_session
from tools.log_utils import log_call
from tools.tasks import _get_or_create_tags


def _goal_dict(goal: Goal) -> dict:
    return {
        "id": goal.id,
        "title": goal.title,
        "description": goal.description,
        "target_date": goal.target_date.isoformat() if goal.target_date else None,
        "status": goal.status,
        "tags": [t.name for t in goal.tags],
        "parent_goal_id": goal.parent_goal_id,
    }


def create_goal(
    title: str,
    description: str = "",
    target_date: str = "",
    tag_names: list[str] | None = None,
) -> str:
    """Create a new active top-level goal.

    Tasks tagged with any of the goal's tags join it through tag membership.

    Args:
        title: Goal title (1-255 characters).
        description: Optional extended description.
        target_date: Optional ISO-8601 date string (YYYY-MM-DD).
        tag_names: Optional list of tag names (max 5, will be normalized).

    Returns:
        JSON-encoded dict with the created goal or an error.
    """
    tag_names = tag_names or []
    params = {"title": title, "description": description,
              "target_date": target_date, "tag_names": tag_names}
    try:
        if not title.strip() or len(title) > 255:
            raise ValueError("title must be 1-255 characters")
        target = date.fromisoformat(target_date) if target_date else None
        validate_tag_count(tag_names)
        with get_session() as session:
            goal = Goal(
                title=title,
                description=description or None,
                target_date=target,
                status="active",
                parent_goal_id=None,
                created_at=datetime.now(UTC),
            )
            goal.tags = _get_or_create_tags(session, tag_names)
            session.add(goal)
            session.flush()
            result_json = json.dumps(_goal_dict(goal))
        log_call("create_goal", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("create_goal", params, error_json, "error")
        return error_json


def list_goals(tag: str = "", include_archived: bool = False) -> str:
    """List goals, optionally filtered by tag.

    Args:
        tag: Optional tag name; normalized before matching.
        include_archived: Include archived goals (default False).

    Returns:
        JSON-encoded list of goals (id, title, status, target_date, tags,
        archived_at) ordered by id, or an error.
    """
    params = {"tag": tag, "include_archived": include_archived}
    try:
        with get_session() as session:
            query = session.query(Goal)
            if not include_archived:
                query = query.filter(Goal.archived_at.is_(None))
            if tag:
                query = query.filter(Goal.tags.any(Tag.name == normalize_tag_name(tag)))
            result = [
                {
                    "id": g.id,
                    "title": g.title,
                    "status": g.status,
                    "target_date": g.target_date.isoformat() if g.target_date else None,
                    "tags": [t.name for t in g.tags],
                    "archived_at": g.archived_at.isoformat() if g.archived_at else None,
                }
                for g in query.order_by(Goal.id).all()
            ]
        result_json = json.dumps(result)
        log_call("list_goals", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("list_goals", params, error_json, "error")
        return error_json


def get_goal(goal_id: int) -> str:
    """Return a goal with every task it rolls up, scheduled or backlog.

    Mirrors GET /api/goals/{id}: tasks carrying ALL of the goal's tags plus
    directly linked tasks, deduped. Sub-goals are listed, not expanded.

    Returns:
        JSON-encoded goal dict with ``archived_at``, ``tasks`` (id, title,
        description, status, category, day, tags) and ``sub_goals``
        (id, title, status), or an error.
    """
    params = {"goal_id": goal_id}
    try:
        with get_session() as session:
            goal = session.get(Goal, goal_id)
            if goal is None:
                raise ValueError(f"Goal {goal_id} not found")
            task_ids = {t.id for t in goal.direct_tasks}
            if goal.tags:
                task_ids |= set(session.scalars(
                    select(task_tags_table.c.task_id)
                    .where(task_tags_table.c.tag_id.in_([t.id for t in goal.tags]))
                    .group_by(task_tags_table.c.task_id)
                    .having(func.count(task_tags_table.c.tag_id) == len(goal.tags))
                ))
            tasks = (
                session.query(Task).filter(Task.id.in_(task_ids)).order_by(Task.id).all()
            )
            result = {
                **_goal_dict(goal),
                "archived_at": (
                    goal.archived_at.isoformat() if goal.archived_at else None
                ),
                "tasks": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "description": t.description,
                        "status": t.status,
                        "category": t.category,
                        "day": t.day.date.isoformat() if t.day else None,
                        "tags": [tg.name for tg in t.tags],
                    }
                    for t in tasks
                ],
                "sub_goals": [
                    {"id": g.id, "title": g.title, "status": g.status}
                    for g in sorted(goal.sub_goals, key=lambda g: g.id)
                ],
            }
        result_json = json.dumps(result)
        log_call("get_goal", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("get_goal", params, error_json, "error")
        return error_json
