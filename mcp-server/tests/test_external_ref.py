"""Tests for linking tasks to tickets in external systems (Jira, Linear, ...).

A sync job finds tasks by (external_source, external_id) to update their status,
so a ref that is lost, mis-normalized, or half-set breaks the link silently.
"""

import json

import tools.tasks as tasks


def test_create_task_stores_normalized_ref_and_find_returns_it(patched_get_session):
    """Source is case-folded so 'Jira' and 'jira' refer to the same system."""
    created = json.loads(
        tasks.create_task("Fix login", "deep_work", external_source=" Jira ", external_id=" POKA-12 ")
    )
    assert created["external_source"] == "jira"
    assert created["external_id"] == "POKA-12"

    found = json.loads(tasks.find_tasks_by_external_ref("JIRA", "POKA-12"))
    assert [t["id"] for t in found] == [created["id"]]
    assert found[0]["status"] == "pending"


def test_backlog_task_ref_is_findable_and_listed(patched_get_session):
    created = json.loads(
        tasks.add_backlog_task("Write docs", external_source="linear", external_id="ENG-7")
    )
    found = json.loads(tasks.find_tasks_by_external_ref("linear", "ENG-7"))
    assert [t["id"] for t in found] == [created["id"]]

    listed = json.loads(tasks.list_backlog())
    assert listed[0]["external_source"] == "linear"
    assert listed[0]["external_id"] == "ENG-7"


def test_same_key_in_another_system_does_not_match(patched_get_session):
    """Jira PROJ-1 and Linear PROJ-1 are different tickets."""
    tasks.create_task("Jira one", "deep_work", external_source="jira", external_id="PROJ-1")
    assert json.loads(tasks.find_tasks_by_external_ref("linear", "PROJ-1")) == []


def test_half_set_ref_is_rejected(patched_get_session):
    """An id without its system (or vice versa) can never be synced, so refuse it."""
    result = json.loads(tasks.create_task("X", "deep_work", external_id="POKA-1"))
    assert "error" in result
    result = json.loads(tasks.add_backlog_task("X", external_source="jira"))
    assert "error" in result
    assert json.loads(tasks.list_backlog()) == []


def test_task_without_ref_still_works(patched_get_session):
    created = json.loads(tasks.create_task("Plain", "short_task"))
    assert created["external_source"] is None
    assert created["external_id"] is None


def test_set_daily_plan_keeps_ref_per_task(patched_get_session, monkeypatch, log_calls):
    import tools.daily as daily

    monkeypatch.setattr(daily, "get_session", patched_get_session)
    monkeypatch.setattr(daily, "log_call", lambda *a, **k: log_calls.append(a))
    plan = [{"title": "Ticket", "category": "deep_work", "external_source": "jira", "external_id": "POKA-9"}]
    assert json.loads(daily.set_daily_plan("", json.dumps(plan)))["success"]

    assert len(json.loads(tasks.find_tasks_by_external_ref("jira", "POKA-9"))) == 1


def test_empty_lookup_is_an_error_not_every_unlinked_task(patched_get_session):
    """A blank ref must not match tasks whose ref is NULL and get them all synced."""
    tasks.create_task("Plain", "short_task")
    assert "error" in json.loads(tasks.find_tasks_by_external_ref("", ""))
