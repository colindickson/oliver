"""Oliver MCP server — exposes the 3-3-3 productivity tools over stdio transport."""

import os
import sys

# Ensure the directory containing this file is on sys.path so that the
# ``models``, ``tools``, and ``db`` packages are importable when the server
# is launched from any working directory (including Docker's /app).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

from tools.analytics import get_analytics
from tools.daily import get_daily_plan, set_daily_plan
from tools.tasks import complete_task, create_task, delete_task, update_task
from tools.timer import start_timer, stop_timer

mcp = FastMCP("Oliver")


@mcp.tool()
def get_daily_plan_tool(date: str = "") -> str:
    """Get the daily plan (tasks) for a given date. Defaults to today. Date format: YYYY-MM-DD"""
    return get_daily_plan(date)


@mcp.tool()
def set_daily_plan_tool(date: str, tasks: str) -> str:
    """Replace all tasks for a date. tasks must be a JSON array string like: '[{"title":"Task","category":"deep_work"}]'"""
    return set_daily_plan(date, tasks)


@mcp.tool()
def create_task_tool(
    title: str,
    category: str,
    day_date: str = "",
    description: str = "",
    tags: list[str] | None = None,
) -> str:
    """Create a task. category must be: deep_work, short_task, or maintenance.
    day_date defaults to today (YYYY-MM-DD). tags is an optional list of tag strings (max 5)."""
    return create_task(title, category, day_date, description, tags or [])


@mcp.tool()
def update_task_tool(
    task_id: int,
    title: str = "",
    description: str = "",
    status: str = "",
    tags: list[str] | None = None,
) -> str:
    """Update a task by ID. Provide only the fields to change.
    tags: omit to leave unchanged, pass [] to clear all tags, pass list to replace (max 5)."""
    return update_task(task_id, title, description, status, tags)


@mcp.tool()
def delete_task_tool(task_id: int) -> str:
    """Delete a task by ID."""
    return delete_task(task_id)


@mcp.tool()
def complete_task_tool(task_id: int) -> str:
    """Mark a task as completed."""
    return complete_task(task_id)


@mcp.tool()
def start_timer_tool(task_id: int) -> str:
    """Start the timer for a task. Resumes accumulated time if paused on the same task."""
    return start_timer(task_id)


@mcp.tool()
def stop_timer_tool(task_id: int) -> str:
    """Stop the running timer and record the session."""
    return stop_timer(task_id)


@mcp.tool()
def get_analytics_tool(days: int = 30) -> str:
    """Get productivity analytics for the past N days."""
    return get_analytics(days)


if __name__ == "__main__":
    mcp.run()
