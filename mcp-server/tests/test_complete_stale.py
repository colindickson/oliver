"""Tests for tools.tasks.complete_stale_tasks.

Lets an LLM clear forgotten board tasks in one call instead of N complete_task calls.
"""

import json
from datetime import date, timedelta

import tools.tasks as tasks
from models.day import Day
from models.task import Task


def _task(session, title, d=None, status="pending"):
    day = None
    if d is not None:
        day = Day(date=d)
        session.add(day)
        session.flush()
    session.add(Task(title=title, day_id=day.id if day else None, status=status, order_index=0))


def test_sweeps_only_old_scheduled_unfinished_tasks(patched_get_session):
    """Only work left on a board 8+ days ago is forgotten; day-less is real backlog."""
    today = date.today()
    with patched_get_session() as s:
        _task(s, "old pending", today - timedelta(days=8))
        _task(s, "old active", today - timedelta(days=9), status="in_progress")
        _task(s, "7 days ago", today - timedelta(days=7))
        _task(s, "dayless")
        _task(s, "today", today)

    result = json.loads(tasks.complete_stale_tasks(7))

    assert result["completed"] == 2
    with patched_get_session() as s:
        done = {t.title for t in s.query(Task).filter(Task.status == "completed")}
        assert done == {"old pending", "old active"}
        assert all(t.completed_at for t in s.query(Task).filter(Task.status == "completed"))


def test_rejects_non_positive_days(patched_get_session):
    """days=0 would sweep yesterday's live work."""
    with patched_get_session() as s:
        _task(s, "yesterday", date.today() - timedelta(days=1))

    assert "error" in json.loads(tasks.complete_stale_tasks(0))
    with patched_get_session() as s:
        assert s.query(Task).one().status == "pending"
