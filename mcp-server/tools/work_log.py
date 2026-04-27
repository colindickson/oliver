"""Work log tool: record work done on a project for today."""

import json
from datetime import date

from models.work_log import WorkLog
from tools.daily import get_session, _get_or_create_day
from tools.log_utils import log_call
from tools.tasks import _get_or_create_tags
from oliver_shared import validate_tag_count


def log_work(project_name: str, description: str, tags: list[str] | None = None) -> str:
    """Record a work log entry for today.

    Args:
        project_name: Free-text project identifier (e.g. 'oliver', 'client-api').
        description: What was done.
        tags: Optional list of tag names (max 5).

    Returns:
        JSON-encoded dict with the created work log's id, project_name,
        description, created_at, and tags.
    """
    if tags is None:
        tags = []
    params = {"project_name": project_name, "description": description, "tags": tags}

    try:
        validate_tag_count(tags)
    except ValueError as e:
        error_json = json.dumps({"error": str(e)})
        log_call("log_work", params, error_json, "error")
        return error_json

    try:
        with get_session() as session:
            day = _get_or_create_day(session, date.today())
            work_log = WorkLog(
                day_id=day.id,
                project_name=project_name,
                description=description,
            )
            session.add(work_log)
            session.flush()
            if tags:
                work_log.tags = _get_or_create_tags(session, tags)
            session.refresh(work_log)
            result = {
                "id": work_log.id,
                "project_name": work_log.project_name,
                "description": work_log.description,
                "created_at": work_log.created_at.isoformat() if work_log.created_at else None,
                "tags": [t.name for t in work_log.tags],
            }
        result_json = json.dumps(result)
        log_call("log_work", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("log_work", params, error_json, "error")
        return error_json
