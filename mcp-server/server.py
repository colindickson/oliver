from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Oliver")


@mcp.tool()
def get_daily_plan(date: str = "") -> str:
    """Get the daily plan for a given date (defaults to today)."""
    return "Not yet implemented"


@mcp.tool()
def set_daily_plan(date: str, tasks: list) -> str:
    """Set or update the daily plan for a given date."""
    return "Not yet implemented"


@mcp.tool()
def create_task(
    title: str,
    category: str,
    day_date: str = "",
    description: str = "",
) -> str:
    """Create a new task and optionally assign it to a daily plan."""
    return "Not yet implemented"


@mcp.tool()
def update_task(
    task_id: int,
    title: str = "",
    description: str = "",
    status: str = "",
) -> str:
    """Update fields on an existing task."""
    return "Not yet implemented"


@mcp.tool()
def delete_task(task_id: int) -> str:
    """Delete a task by ID."""
    return "Not yet implemented"


@mcp.tool()
def complete_task(task_id: int) -> str:
    """Mark a task as complete."""
    return "Not yet implemented"


@mcp.tool()
def start_timer(task_id: int) -> str:
    """Start the timer for a task."""
    return "Not yet implemented"


@mcp.tool()
def stop_timer(task_id: int) -> str:
    """Stop the running timer for a task."""
    return "Not yet implemented"


@mcp.tool()
def get_analytics(days: int = 30) -> str:
    """Get productivity analytics for the past N days."""
    return "Not yet implemented"


if __name__ == "__main__":
    mcp.run()
