"""Tests for tools.tasks.list_backlog.

The epic skill calls list_backlog(tag=<epic key>) on re-run to skip children
that already have a backlog task, so wrong filtering means duplicates or
skipped tickets.
"""

import json

import tools.tasks as tasks
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
    assert set(result[0]) == {"id", "title", "description", "status", "tags"}
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
