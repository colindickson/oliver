"""MCP tools for managing per-project default tags."""

import json

import models  # noqa: F401 — ensures all ORM models registered
from models.project_default import ProjectDefault
from tools.daily import get_session
from tools.log_utils import log_call
from oliver_shared import MAX_TAGS_PER_TASK


def get_project_defaults(project_name: str = "") -> str:
    """Return default tags for a project, or all projects if project_name is empty.

    Args:
        project_name: Specific project to look up. Pass "" to list all.

    Returns:
        JSON string: single {project_name, default_tags} or list thereof.
    """
    params = {"project_name": project_name}
    try:
        with get_session() as session:
            if project_name:
                pd = session.query(ProjectDefault).filter(
                    ProjectDefault.project_name == project_name
                ).first()
                result = {
                    "project_name": project_name,
                    "default_tags": pd.default_tags if pd else [],
                }
            else:
                rows = session.query(ProjectDefault).order_by(
                    ProjectDefault.project_name
                ).all()
                result = [
                    {"project_name": r.project_name, "default_tags": r.default_tags}
                    for r in rows
                ]
        result_json = json.dumps(result)
        log_call("get_project_defaults", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("get_project_defaults", params, error_json, "error")
        return error_json


def set_project_default_tags(project_name: str, default_tags: list[str]) -> str:
    """Create or replace the default tags for a project.

    Args:
        project_name: The project identifier.
        default_tags: New default tag list (max 5).

    Returns:
        JSON string with {project_name, default_tags} or {error}.
    """
    params = {"project_name": project_name, "default_tags": default_tags}
    if len(default_tags) > MAX_TAGS_PER_TASK:
        error_json = json.dumps({"error": f"At most {MAX_TAGS_PER_TASK} default tags allowed"})
        log_call("set_project_default_tags", params, error_json, "error")
        return error_json
    try:
        with get_session() as session:
            pd = session.query(ProjectDefault).filter(
                ProjectDefault.project_name == project_name
            ).first()
            if pd is None:
                pd = ProjectDefault(project_name=project_name, default_tags=list(default_tags))
                session.add(pd)
            else:
                pd.default_tags = list(default_tags)
            session.flush()
            result = {"project_name": pd.project_name, "default_tags": pd.default_tags}
        result_json = json.dumps(result)
        log_call("set_project_default_tags", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("set_project_default_tags", params, error_json, "error")
        return error_json
