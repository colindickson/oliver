"""Work log tool: record work done on a project for a given date."""

import json
from datetime import date

import models  # noqa: F401 — ensures all ORM models are registered before session use
from models.project_default import ProjectDefault
from models.work_log import WorkLog
from tools.daily import get_session, _get_or_create_day
from tools.log_utils import log_call
from tools.tasks import _get_or_create_tags
from oliver_shared import validate_tag_count, MAX_TAGS_PER_TASK


def log_work(
    project_name: str,
    description: str,
    tags: list[str] | None = None,
    date_str: str = "",
) -> str:
    """Record a work log entry for a given date (defaults to today).

    Args:
        project_name: Free-text project identifier (e.g. 'oliver', 'client-api').
        description: What was done.
        tags: Optional list of tag names (max 5). Project default tags are merged in
              automatically to fill remaining slots.
        date_str: ISO-8601 date (YYYY-MM-DD). Omit or pass "" to log for today.

    Returns:
        JSON-encoded dict with the created work log's id, project_name,
        description, date, created_at, and tags.
    """
    if tags is None:
        tags = []
    params = {"project_name": project_name, "description": description, "tags": tags, "date_str": date_str}

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
        with get_session() as session:
            # Merge in project default tags: provided tags take priority,
            # defaults fill remaining slots up to MAX_TAGS_PER_TASK
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
            work_log = WorkLog(
                day_id=day.id,
                project_name=project_name,
                description=description,
            )
            session.add(work_log)
            session.flush()
            if merged:
                work_log.tags = _get_or_create_tags(session, merged)
            session.refresh(work_log)
            result = {
                "id": work_log.id,
                "project_name": work_log.project_name,
                "description": work_log.description,
                "date": target_date.isoformat(),
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


def batch_log_work(entries: list[dict]) -> str:
    """Atomically record multiple work log entries.

    Each entry dict accepts:
        project_name (str, required)
        description  (str, required)
        tags         (list[str], optional, default [])
        date_str     (str, optional, ISO-8601 YYYY-MM-DD, default "" = today)

    All entries are validated upfront. If any entry fails (bad date, too many
    tags), no entries are saved and an error JSON is returned.

    Returns:
        JSON array of result dicts on success, or {"error": "..."} on failure.
    """
    params = {"entries": entries}

    # --- Upfront validation pass ---
    parsed: list[tuple[str, str, list[str], date]] = []
    for i, entry in enumerate(entries):
        project_name = entry.get("project_name", "")
        description = entry.get("description", "")
        tags = entry.get("tags") or []
        date_str = entry.get("date_str", "")

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

        parsed.append((project_name, description, tags, target_date))

    # --- Single session for all inserts ---
    try:
        with get_session() as session:
            results = []
            for project_name, description, tags, target_date in parsed:
                # Merge project default tags
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
                work_log = WorkLog(
                    day_id=day.id,
                    project_name=project_name,
                    description=description,
                )
                session.add(work_log)
                session.flush()
                if merged:
                    work_log.tags = _get_or_create_tags(session, merged)
                session.refresh(work_log)
                results.append({
                    "id": work_log.id,
                    "project_name": work_log.project_name,
                    "description": work_log.description,
                    "date": target_date.isoformat(),
                    "created_at": work_log.created_at.isoformat() if work_log.created_at else None,
                    "tags": [t.name for t in work_log.tags],
                })
        result_json = json.dumps(results)
        log_call("batch_log_work", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("batch_log_work", params, error_json, "error")
        return error_json
