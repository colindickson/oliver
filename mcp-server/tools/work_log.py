"""Work log tool: record work done on a project for a given date."""

import json
from datetime import date, timedelta

import models  # noqa: F401 — ensures all ORM models are registered before session use
from models.day import Day
from models.project_default import ProjectDefault
from models.work_log import WorkLog
from tools.daily import get_session, _get_or_create_day
from tools.log_utils import log_call
from tools.tasks import _get_or_create_tags
from oliver_shared import validate_tag_count, validate_log_type, MAX_TAGS_PER_TASK


def _normalize_project_name(project_name: str) -> str:
    """Normalize a project name that arrived as an absolute filesystem path.

    Some callers (e.g. hooks that cannot compute basenames) pass a full path
    like ``/Users/cdickson/code/epsilon/poka`` where a bare ``poka`` is meant.
    Only path-like values (starting with ``/`` or ``~``) are reduced to their
    final segment; everything else — plain names, relative ``team/project``
    names, and degenerate inputs like ``/`` or ``""`` — is returned unchanged.
    """
    if not project_name or not project_name.strip():
        return project_name
    if not project_name.startswith(("/", "~")):
        return project_name
    stripped = project_name.rstrip("/")
    segment = stripped.rsplit("/", 1)[-1]
    if not segment or segment == "~":
        return project_name
    return segment


def _create_work_log_in_session(
    session,
    project_name: str,
    description: str,
    tags: list[str],
    target_date: date,
    log_type: str | None = None,
) -> dict:
    project_name = _normalize_project_name(project_name)
    pd = session.query(ProjectDefault).filter(
        ProjectDefault.project_name == project_name
    ).first()
    default_tags: list[str] = pd.default_tags if pd else []
    provided_lower = {t.lower() for t in tags}
    merged = list(tags)
    for dt in default_tags:
        if dt.lower() not in provided_lower and len(merged) < MAX_TAGS_PER_TASK:
            merged.append(dt)
    day = _get_or_create_day(session, target_date)
    work_log = WorkLog(day_id=day.id, project_name=project_name, description=description, log_type=log_type)
    session.add(work_log)
    session.flush()
    if merged:
        work_log.tags = _get_or_create_tags(session, merged)
    session.refresh(work_log)
    return {
        "id": work_log.id,
        "project_name": work_log.project_name,
        "description": work_log.description,
        "log_type": work_log.log_type,
        "date": target_date.isoformat(),
        "created_at": work_log.created_at.isoformat() if work_log.created_at else None,
        "tags": [t.name for t in work_log.tags],
    }


def log_work(
    project_name: str,
    description: str,
    tags: list[str] | None = None,
    date_str: str = "",
    log_type: str | None = None,
) -> str:
    """Record a work log entry for a given date (defaults to today).

    Args:
        project_name: Free-text project identifier (e.g. 'oliver', 'client-api').
        description: What was done.
        tags: Optional list of tag names (max 5). Project default tags are merged in
              automatically to fill remaining slots.
        date_str: ISO-8601 date (YYYY-MM-DD). Omit or pass "" to log for today.
        log_type: Optional activity type: 'commit', 'pr', 'review', or 'research'.

    Returns:
        JSON-encoded dict with the created work log's id, project_name,
        description, log_type, date, created_at, and tags.
    """
    if tags is None:
        tags = []
    params = {"project_name": project_name, "description": description, "tags": tags, "date_str": date_str, "log_type": log_type}

    if date_str:
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            error_json = json.dumps({"error": f"Invalid date format '{date_str}'. Use YYYY-MM-DD."})
            log_call("log_work", params, error_json, "error")
            return error_json
    else:
        target_date = date.today()

    try:
        validate_tag_count(tags)
    except ValueError as e:
        error_json = json.dumps({"error": str(e)})
        log_call("log_work", params, error_json, "error")
        return error_json

    try:
        validate_log_type(log_type)
    except ValueError as e:
        error_json = json.dumps({"error": str(e)})
        log_call("log_work", params, error_json, "error")
        return error_json

    try:
        with get_session() as session:
            result = _create_work_log_in_session(session, project_name, description, tags, target_date, log_type=log_type)
        result_json = json.dumps(result)
        log_call("log_work", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("log_work", params, error_json, "error")
        return error_json


def batch_log_work(entries: list[dict]) -> str:
    """Atomically record multiple work log entries.

    Each entry dict accepts:
        project_name (str, required)
        description  (str, required)
        tags         (list[str], optional, default [])
        date_str     (str, optional, ISO-8601 YYYY-MM-DD, default "" = today)
        log_type     (str, optional, one of: commit, pr, review, research)

    All entries are validated upfront. If any entry fails (bad date, too many
    tags, invalid log_type), no entries are saved and an error JSON is returned.

    Returns:
        JSON array of result dicts on success, or {"error": "..."} on failure.
    """
    params = {"entries": entries}

    # --- Upfront validation pass ---
    parsed: list[tuple[str, str, list[str], date, str | None]] = []
    for i, entry in enumerate(entries):
        project_name = entry.get("project_name", "")
        description = entry.get("description", "")
        tags = entry.get("tags") or []
        date_str = entry.get("date_str", "")
        log_type = entry.get("log_type")

        if not project_name:
            error_json = json.dumps({"error": f"Entry {i}: 'project_name' is required."})
            log_call("batch_log_work", params, error_json, "error")
            return error_json
        if not description:
            error_json = json.dumps({"error": f"Entry {i}: 'description' is required."})
            log_call("batch_log_work", params, error_json, "error")
            return error_json

        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                error_json = json.dumps(
                    {"error": f"Entry {i}: invalid date format '{date_str}'. Use YYYY-MM-DD."}
                )
                log_call("batch_log_work", params, error_json, "error")
                return error_json
        else:
            target_date = date.today()

        try:
            validate_tag_count(tags)
        except ValueError as e:
            error_json = json.dumps({"error": f"Entry {i} ('{project_name}'): {e}"})
            log_call("batch_log_work", params, error_json, "error")
            return error_json

        try:
            validate_log_type(log_type)
        except ValueError as e:
            error_json = json.dumps({"error": f"Entry {i} ('{project_name}'): {e}"})
            log_call("batch_log_work", params, error_json, "error")
            return error_json

        parsed.append((project_name, description, tags, target_date, log_type))

    # --- Single session for all inserts ---
    try:
        with get_session() as session:
            results = []
            for project_name, description, tags, target_date, log_type in parsed:
                result = _create_work_log_in_session(session, project_name, description, tags, target_date, log_type=log_type)
                results.append(result)
        result_json = json.dumps(results)
        log_call("batch_log_work", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("batch_log_work", params, error_json, "error")
        return error_json


def get_work_logs(
    start_date_str: str = "",
    end_date_str: str = "",
    log_type: str | None = None,
) -> str:
    """Retrieve work logs within a date range, optionally filtered by type.

    Args:
        start_date_str: ISO-8601 date (YYYY-MM-DD). Defaults to 7 days ago.
        end_date_str:   ISO-8601 date (YYYY-MM-DD). Defaults to today.
        log_type:       Optional filter — one of: commit, pr, review, research.

    Returns:
        JSON array of work log dicts on success, or {"error": "..."} on failure.
    """
    params = {"start_date_str": start_date_str, "end_date_str": end_date_str, "log_type": log_type}

    if start_date_str:
        try:
            start = date.fromisoformat(start_date_str)
        except ValueError:
            error_json = json.dumps({"error": f"Invalid date format '{start_date_str}'. Use YYYY-MM-DD."})
            log_call("get_work_logs", params, error_json, "error")
            return error_json
    else:
        start = date.today() - timedelta(days=6)

    if end_date_str:
        try:
            end = date.fromisoformat(end_date_str)
        except ValueError:
            error_json = json.dumps({"error": f"Invalid date format '{end_date_str}'. Use YYYY-MM-DD."})
            log_call("get_work_logs", params, error_json, "error")
            return error_json
    else:
        end = date.today()

    if log_type is not None:
        try:
            validate_log_type(log_type)
        except ValueError as e:
            error_json = json.dumps({"error": str(e)})
            log_call("get_work_logs", params, error_json, "error")
            return error_json

    try:
        with get_session() as session:
            q = (
                session.query(WorkLog, Day.date)
                .join(Day, WorkLog.day_id == Day.id)
                .filter(Day.date >= start, Day.date <= end)
            )
            if log_type is not None:
                q = q.filter(WorkLog.log_type == log_type)
            rows = q.order_by(Day.date.desc(), WorkLog.created_at.desc()).all()
            results = []
            for wl, day_date in rows:
                results.append({
                    "id": wl.id,
                    "date": day_date.isoformat() if day_date else None,
                    "project_name": wl.project_name,
                    "description": wl.description,
                    "log_type": wl.log_type,
                    "tags": [t.name for t in wl.tags],
                    "created_at": wl.created_at.isoformat() if wl.created_at else None,
                })
        result_json = json.dumps(results)
        log_call("get_work_logs", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("get_work_logs", params, error_json, "error")
        return error_json
