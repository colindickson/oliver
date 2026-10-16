"""Tests for tools.tasks.list_backlog.

The epic skill calls list_backlog(tag=<epic key>) on re-run to skip children
that already have a backlog task, so wrong filtering means duplicates or
skipped tickets.
"""

import json
from datetime import date, timedelta

import tools.tasks as tasks
from models.day import Day
from models.task import Task


def _add_backlog(patched_get_session, title, tags=(), order_index=0):
    """Insert a backlog task (day_id NULL) directly, with normalized tags."""
    with patched_get_session() as session:
        task = Task(title=title, day_id=None, order_index=order_index)
        session.add(task)
        session.flush()
        task.tags = tasks._get_or_create_tags(session, list(tags))


def _titles(result_json):
    return [t["title"] for t in json.loads(result_json)]


def test_tag_filter_returns_only_matching_backlog_tasks(patched_get_session):
    """Day-assigned or other-epic tasks must not count as 'already created'."""
    _add_backlog(patched_get_session, "POKA-1001 Fix thing", ["poka-12345"])
    _add_backlog(patched_get_session, "OTHER-1 Unrelated", ["other-epic"])
    tasks.create_task("POKA-1002 Scheduled", "deep_work", tags=["poka-12345"])

    result = json.loads(tasks.list_backlog(tag="POKA-12345"))

    assert [t["title"] for t in result] == ["POKA-1001 Fix thing"]
    assert set(result[0]) == {
        "id", "title", "description", "status", "tags", "day", "external_source", "external_id",
    }
    assert result[0]["tags"] == ["poka-12345"]


def test_search_is_case_insensitive(patched_get_session):
    """Ticket keys may differ in case between Jira and stored titles."""
    _add_backlog(patched_get_session, "POKA-1001 Fix thing")
    assert _titles(tasks.list_backlog(search="poka-1")) == ["POKA-1001 Fix thing"]


def test_search_wildcards_are_literal(patched_get_session):
    """'%' and '_' in a title must not act as SQL wildcards and match other tickets."""
    _add_backlog(patched_get_session, "500 items")
    _add_backlog(patched_get_session, "50% done", order_index=1)
    _add_backlog(patched_get_session, "a_b", order_index=2)
    _add_backlog(patched_get_session, "axb", order_index=3)

    assert _titles(tasks.list_backlog(search="50%")) == ["50% done"]
    assert _titles(tasks.list_backlog(search="a_b")) == ["a_b"]


def test_results_ordered_by_order_index(patched_get_session):
    """Backlog order is user-visible priority and must be preserved."""
    _add_backlog(patched_get_session, "second", order_index=2)
    _add_backlog(patched_get_session, "first", order_index=1)
    assert _titles(tasks.list_backlog()) == ["first", "second"]


def test_success_is_logged(patched_get_session, log_calls):
    """Audit log must record the call."""
    tasks.list_backlog(tag="x")
    assert log_calls[-1][0] == "list_backlog"
    assert log_calls[-1][3] == "success"


def test_error_is_logged_and_returned(patched_get_session, log_calls, monkeypatch):
    """A DB failure must surface as an error, not an empty list (-> duplicates)."""

    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(tasks, "get_session", boom)
    result = json.loads(tasks.list_backlog(tag="x"))
    assert "db down" in result["error"]
    assert log_calls[-1][0] == "list_backlog"
    assert log_calls[-1][3] == "error"


def _add_on_day(patched_get_session, title, offset_days, status="pending", rolled_from=None):
    """Insert a task on the day ``today + offset_days`` (date.today(), as the backend)."""
    with patched_get_session() as session:
        d = date.today() + timedelta(days=offset_days)
        day = session.query(Day).filter_by(date=d).first() or Day(date=d)
        session.add(day)
        session.flush()
        task = Task(
            title=title, day_id=day.id, status=status, category="deep_work",
            rolled_from_task_id=rolled_from,
        )
        session.add(task)
        session.flush()
        return task.id


def test_idle_past_and_future_tasks_listed_with_day_in_backend_order(patched_get_session):
    """Backlog == idle work: stale (past) and planned (future) tasks appear with
    their ``day``; order is day-less, past newest-first, future soonest-first,
    mirroring GET /api/backlog so both surfaces agree."""
    _add_on_day(patched_get_session, "future far", 5)
    _add_on_day(patched_get_session, "past old", -10)
    _add_on_day(patched_get_session, "future soon", 2)
    _add_on_day(patched_get_session, "past recent", -1)
    _add_backlog(patched_get_session, "no day")

    result = json.loads(tasks.list_backlog())

    assert [t["title"] for t in result] == [
        "no day", "past recent", "past old", "future soon", "future far"
    ]
    assert result[0]["day"] is None
    assert result[1]["day"] == (date.today() - timedelta(days=1)).isoformat()


def test_non_idle_tasks_are_excluded(patched_get_session):
    """Each excluded case fails if the hand-copied predicate drifts from the
    backend: today's tasks, finished tasks, rolled-forward tasks, and an original
    that already has a continuation (only the continuation is listed)."""
    _add_on_day(patched_get_session, "today", 0)
    _add_on_day(patched_get_session, "done past", -3, status="completed")
    _add_on_day(patched_get_session, "rolled past", -3, status="rolled_forward")
    _add_backlog(patched_get_session, "done no day")
    with patched_get_session() as session:
        session.query(Task).filter_by(title="done no day").one().status = "completed"
    original = _add_on_day(patched_get_session, "original", -4)
    _add_on_day(patched_get_session, "continuation", 0, rolled_from=original)
    _add_on_day(patched_get_session, "continuation idle", 3, rolled_from=_add_on_day(
        patched_get_session, "original2", -4))

    assert _titles(tasks.list_backlog()) == ["continuation idle"]


def test_include_completed_restores_completed_dayless_tasks(patched_get_session):
    """The epic skill dedupes children via list_backlog(tag=...); completed
    day-less children must stay visible to it or a re-run recreates them."""
    _add_backlog(patched_get_session, "done child")
    with patched_get_session() as session:
        session.query(Task).filter_by(title="done child").one().status = "completed"
    _add_on_day(patched_get_session, "rolled", -2, status="rolled_forward")

    _add_on_day(patched_get_session, "idle past", -3)
    _add_on_day(patched_get_session, "done past", -3, status="completed")

    assert _titles(tasks.list_backlog()) == ["idle past"]
    # The flag adds to the idle set; it must not hide idle work or dump history.
    assert _titles(tasks.list_backlog(include_completed=True)) == ["done child", "idle past"]
