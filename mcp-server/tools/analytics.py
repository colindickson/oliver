"""Analytics tool: aggregate productivity metrics over a rolling date window."""

import json
from datetime import date, timedelta

from models.day import Day
from models.day_off import DayOff
from models.task import Task
from models.timer_session import TimerSession
from tools.daily import get_session


def get_analytics(days: int = 30) -> str:
    """Compute productivity analytics for the past *days* calendar days.

    Metrics include total tasks tracked, completed tasks, a completion rate
    percentage, and total time spent (in seconds) broken down by task category.

    Args:
        days: Number of calendar days to look back from today (inclusive).

    Returns:
        JSON-encoded dict with the following keys:

        - ``period_days``: The requested look-back window.
        - ``total_days_tracked``: Number of Day rows found in the window.
        - ``total_tasks``: Sum of all tasks across those days.
        - ``completed_tasks``: Count of tasks with ``status == "completed"``.
        - ``completion_rate_pct``: Integer percentage (0-100).
        - ``category_time_seconds``: Dict mapping each category name to its
          total recorded timer seconds.
    """
    cutoff = date.today() - timedelta(days=days)
    with get_session() as session:
        off_day_ids = {row.day_id for row in session.query(DayOff).all()}
        day_rows = session.query(Day).filter(Day.date >= cutoff).all()
        day_rows = [d for d in day_rows if d.id not in off_day_ids]
        total_days = len(day_rows)
        completed_tasks = 0
        total_tasks = 0
        category_seconds: dict[str, int] = {
            "deep_work": 0,
            "short_task": 0,
            "maintenance": 0,
        }

        for day in day_rows:
            tasks = session.query(Task).filter(Task.day_id == day.id).all()
            total_tasks += len(tasks)
            completed_tasks += sum(1 for t in tasks if t.status == "completed")
            for task in tasks:
                timer_sessions = (
                    session.query(TimerSession)
                    .filter(TimerSession.task_id == task.id)
                    .all()
                )
                for ts in timer_sessions:
                    if ts.duration_seconds:
                        category_seconds[task.category] = (
                            category_seconds.get(task.category, 0) + ts.duration_seconds
                        )

        completion_rate = (
            round(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        result = {
            "period_days": days,
            "total_days_tracked": total_days,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate_pct": completion_rate,
            "category_time_seconds": category_seconds,
        }
    return json.dumps(result, indent=2)
