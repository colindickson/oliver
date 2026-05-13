"""Analytics tool: aggregate productivity metrics over a rolling date window."""

import json
from datetime import date, timedelta

from sqlalchemy import func, select

from models.day import Day
from models.day_off import DayOff
from models.task import Task
from models.timer_session import TimerSession
from tools.daily import get_session
from tools.log_utils import log_call
from oliver_shared import CATEGORY_DEEP_WORK, CATEGORY_MAINTENANCE, CATEGORY_SHORT_TASK, STATUS_COMPLETED


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
    params = {"days": days}
    try:
        cutoff = date.today() - timedelta(days=days)
        with get_session() as session:
            # Subquery for off-day IDs — excluded from all metrics
            off_day_ids_subq = select(DayOff.day_id).scalar_subquery()

            # Single query: count of qualifying days in the window
            total_days: int = session.execute(
                select(func.count(Day.id))
                .where(Day.date >= cutoff)
                .where(Day.id.not_in(off_day_ids_subq))
            ).scalar_one() or 0

            # Two aggregate queries: total tasks and completed tasks
            base_task_query = (
                select(func.count(Task.id))
                .join(Day, Task.day_id == Day.id)
                .where(Day.date >= cutoff)
                .where(Day.id.not_in(off_day_ids_subq))
            )

            total_tasks: int = session.execute(base_task_query).scalar_one() or 0

            completed_tasks: int = session.execute(
                base_task_query.where(Task.status == STATUS_COMPLETED)
            ).scalar_one() or 0

            # Single query: sum timer seconds grouped by task category
            category_seconds: dict[str, int] = {
                CATEGORY_DEEP_WORK: 0,
                CATEGORY_SHORT_TASK: 0,
                CATEGORY_MAINTENANCE: 0,
            }

            category_rows = session.execute(
                select(
                    Task.category,
                    func.sum(TimerSession.duration_seconds).label("total_seconds"),
                )
                .join(TimerSession, TimerSession.task_id == Task.id)
                .join(Day, Task.day_id == Day.id)
                .where(Day.date >= cutoff)
                .where(Day.id.not_in(off_day_ids_subq))
                .where(TimerSession.duration_seconds.isnot(None))
                .group_by(Task.category)
            ).all()

            for row in category_rows:
                if row.category is not None:
                    category_seconds[row.category] = (
                        category_seconds.get(row.category, 0) + int(row.total_seconds or 0)
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
        result_json = json.dumps(result, indent=2)
        log_call("get_analytics", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("get_analytics", params, error_json, "error")
        return error_json
