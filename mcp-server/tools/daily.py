"""Daily plan tools: retrieve and replace the full set of tasks for a given date."""

import json
from contextlib import contextmanager
from datetime import date, datetime, timezone

from db import SessionLocal
from models.daily_note import DailyNote
from models.day import Day
from models.day_rating import DayRating
from models.roadblock import Roadblock
from models.task import Task, STATUS_PENDING


@contextmanager
def get_session():
    """Yield a SQLAlchemy session, committing on success and rolling back on error."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _get_or_create_day(session, target_date: date) -> Day:
    """Return the Day row for *target_date*, creating it if it does not exist.

    Args:
        session: An active SQLAlchemy session.
        target_date: The calendar date to look up or create.

    Returns:
        The persisted Day ORM object (flushed but not yet committed).
    """
    day = session.query(Day).filter(Day.date == target_date).first()
    if day is None:
        day = Day(
            date=target_date,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(day)
        session.flush()
    return day


def get_daily_plan(date_str: str = "") -> str:
    """Return the daily plan for *date_str* (or today) as a JSON string.

    Args:
        date_str: ISO-8601 date string (YYYY-MM-DD). Defaults to today when empty.

    Returns:
        JSON-encoded dict with ``date``, ``day_id``, and ``tasks`` fields.
    """
    target = date.fromisoformat(date_str) if date_str else date.today()
    with get_session() as session:
        day = _get_or_create_day(session, target)
        tasks = (
            session.query(Task)
            .filter(Task.day_id == day.id)
            .order_by(Task.order_index)
            .all()
        )
        note = session.query(DailyNote).filter(DailyNote.day_id == day.id).first()
        roadblock = session.query(Roadblock).filter(Roadblock.day_id == day.id).first()
        rating = session.query(DayRating).filter(DayRating.day_id == day.id).first()

        result = {
            "date": day.date.isoformat(),
            "day_id": day.id,
            "tasks": [
                {
                    "id": t.id,
                    "category": t.category,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "order_index": t.order_index,
                    "tags": [tag.name for tag in t.tags],
                }
                for t in tasks
            ],
            "notes": note.content if note else None,
            "roadblocks": roadblock.content if roadblock else None,
            "rating": {
                "focus": rating.focus,
                "energy": rating.energy,
                "satisfaction": rating.satisfaction,
            } if rating else None,
        }
    return json.dumps(result, indent=2)


def set_daily_plan(date_str: str, tasks_json: str) -> str:
    """Replace all tasks for a day with the provided list.

    Existing tasks are deleted before the new set is inserted so the
    caller always has full control over the day's contents.

    Args:
        date_str: ISO-8601 date string (YYYY-MM-DD).
        tasks_json: JSON-encoded array of task dicts. Each dict must contain
            at minimum a ``title`` key. ``category`` defaults to
            ``short_task`` when omitted.

    Returns:
        JSON-encoded dict with ``success``, ``date``, and ``tasks_count``.
    """
    target = date.fromisoformat(date_str) if date_str else date.today()
    try:
        new_tasks = json.loads(tasks_json) if isinstance(tasks_json, str) else tasks_json
    except (json.JSONDecodeError, TypeError):
        return json.dumps({"error": "tasks must be a JSON array string"})

    with get_session() as session:
        day = _get_or_create_day(session, target)
        # Delete existing tasks for the day before inserting the replacement set.
        session.query(Task).filter(Task.day_id == day.id).delete()
        for i, t in enumerate(new_tasks):
            task = Task(
                day_id=day.id,
                category=t.get("category", "short_task"),
                title=t["title"],
                description=t.get("description"),
                status=STATUS_PENDING,
                order_index=i,
            )
            session.add(task)

    return json.dumps(
        {"success": True, "date": target.isoformat(), "tasks_count": len(new_tasks)}
    )
