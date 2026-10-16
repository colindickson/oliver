"""Tests for tools.daily.set_daily_plan.

Idle work (pending/in_progress) on a day may be a continuation picked from the
backlog; deleting it would strand its rolled_forward original with no live
copy, so replacing a day's plan must send it back to the backlog instead.
"""

import json
from datetime import date

import pytest

import tools.daily as daily
import tools.tasks as tasks
from models.day import Day
from models.task import Task


@pytest.fixture
def plan_session(patched_get_session, monkeypatch, log_calls):
    """Also point tools.daily (set_daily_plan's own module) at the test DB."""
    monkeypatch.setattr(daily, "get_session", patched_get_session)
    monkeypatch.setattr(daily, "log_call", lambda *a, **k: log_calls.append(a))
    return patched_get_session


def test_replace_keeps_unfinished_in_backlog_and_deletes_finished(plan_session):
    """Idle work must never be silently destroyed by replacing the plan."""
    with plan_session() as session:
        day = Day(date=date.today())
        session.add(day)
        session.flush()
        keep = Task(day_id=day.id, category="deep_work", title="keep", status="pending")
        doing = Task(day_id=day.id, category="deep_work", title="doing", status="in_progress")
        done = Task(day_id=day.id, category="deep_work", title="done", status="completed")
        session.add_all([keep, doing, done])
        session.flush()
        keep_id, doing_id = keep.id, doing.id

    result = json.loads(
        daily.set_daily_plan(date.today().isoformat(), json.dumps([{"title": "new"}]))
    )
    assert result["tasks_count"] == 1

    with plan_session() as session:
        kept = session.get(Task, keep_id)
        assert (kept.day_id, kept.category, kept.status) == (None, None, "pending")
        moving = session.get(Task, doing_id)
        assert (moving.day_id, moving.category, moving.status) == (None, None, "in_progress")
        # SQLite may reuse the deleted id for the new task, so check by title.
        assert session.query(Task).filter(Task.title == "done").count() == 0
        assert [t.title for t in session.query(Task).filter(Task.day_id.isnot(None))] == ["new"]

    assert {"keep", "doing"} <= {t["title"] for t in json.loads(tasks.list_backlog())}


def test_bad_ref_in_plan_leaves_the_day_untouched(plan_session):
    """A malformed item must never empty the day.

    A bad item must leave the day exactly as it was, whether it is caught by
    the ref pre-validation pass or, if validation ever moves after the detach,
    by the session rolling back. Either way, one bad item must not wipe the
    existing plan.
    """
    with plan_session() as session:
        day = Day(date=date.today())
        session.add(day)
        session.flush()
        old = Task(day_id=day.id, category="deep_work", title="old", status="pending")
        session.add(old)
        session.flush()
        old_id, day_id = old.id, day.id

    result = json.loads(
        daily.set_daily_plan(
            date.today().isoformat(),
            json.dumps([{"title": "ok"}, {"title": "bad", "external_id": "POKA-1"}]),
        )
    )
    assert "error" in result

    with plan_session() as session:
        kept = session.get(Task, old_id)
        assert (kept.day_id, kept.category) == (day_id, "deep_work")
        assert session.query(Task).filter(Task.title.in_(["ok", "bad"])).count() == 0
