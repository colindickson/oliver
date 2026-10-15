"""Tests for create_goal / list_goals (the Jira-epic -> Oliver-goal skill)."""

import json
from datetime import UTC, datetime

from models.goal import Goal
from models.tag import Tag
from models.task import Task
from tools.goals import create_goal, get_goal, list_goals
from tools.tasks import add_backlog_task, create_task


def _goal_count(get_session):
    with get_session() as session:
        return session.query(Goal).count()


def test_create_goal_tag_is_shared_with_backlog_tasks(patched_get_session):
    """Tasks join the goal via the shared Tag row, so the epic key
    must resolve to ONE tag."""
    goal = json.loads(create_goal("Epic", tag_names=["POKA-12345"]))
    assert goal["tags"] == ["poka-12345"]
    assert goal["status"] == "active"
    assert goal["parent_goal_id"] is None

    add_backlog_task("Child task", tags=["POKA-12345"])

    with patched_get_session() as session:
        tags = session.query(Tag).filter(Tag.name == "poka-12345").all()
        assert len(tags) == 1
        assert session.get(Goal, goal["id"]).tags[0].id == tags[0].id


def test_create_goal_returns_fields(patched_get_session):
    """The skill echoes the returned goal back, so every field must be right."""
    goal = json.loads(create_goal("Epic", description="", target_date="2026-12-31"))
    assert goal["target_date"] == "2026-12-31"
    assert goal["description"] is None
    assert goal["tags"] == []


def test_create_goal_description_round_trips(patched_get_session):
    """Epic summaries are stored as the goal description and must come back intact."""
    goal = json.loads(create_goal("Epic", description="Ship the thing"))
    assert goal["description"] == "Ship the thing"
    with patched_get_session() as session:
        assert session.get(Goal, goal["id"]).description == "Ship the thing"


def test_create_goal_validation_errors_write_nothing(patched_get_session, log_calls):
    """A rejected import must not leave a half-made goal a re-run would reuse."""
    cases = [
        {"title": "x", "tag_names": ["a", "b", "c", "d", "e", "f"]},
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 256},
        {"title": "x", "target_date": "31/12/2026"},
    ]
    for kwargs in cases:
        assert "error" in json.loads(create_goal(**kwargs))
    assert _goal_count(patched_get_session) == 0
    assert [c[3] for c in log_calls] == ["error"] * len(cases)


def test_list_goals_tag_filter_is_case_insensitive(patched_get_session):
    """Re-runs look up the epic by its Jira key as typed (upper case)."""
    create_goal("Epic", tag_names=["POKA-12345"])
    create_goal("Other", tag_names=["poka-99999"])
    for tag in ("POKA-12345", "poka-12345"):
        goals = json.loads(list_goals(tag=tag))
        assert [g["title"] for g in goals] == ["Epic"]
    assert len(json.loads(list_goals())) == 2


def test_list_goals_excludes_archived_by_default(patched_get_session):
    """An archived goal must not be reused on re-run, but stays inspectable."""
    gid = json.loads(create_goal("Old", tag_names=["poka-1"]))["id"]
    with patched_get_session() as session:
        session.get(Goal, gid).archived_at = datetime.now(UTC)
    assert json.loads(list_goals(tag="poka-1")) == []
    goals = json.loads(list_goals(tag="poka-1", include_archived=True))
    assert [g["id"] for g in goals] == [gid]
    assert goals[0]["archived_at"] is not None


def test_log_call_success_and_error(patched_get_session, log_calls):
    """Every MCP call must be audited, including failures."""
    create_goal("Epic")
    list_goals()
    create_goal("")
    names_statuses = [(c[0], c[3]) for c in log_calls]
    assert names_statuses == [
        ("create_goal", "success"),
        ("list_goals", "success"),
        ("create_goal", "error"),
    ]


def test_list_goals_error_is_returned_and_logged(monkeypatch, log_calls):
    """A DB failure must surface as an error the skill can report, and be audited."""

    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr("tools.goals.get_session", boom)
    monkeypatch.setattr("tools.goals.log_call", lambda *a, **k: log_calls.append(a))
    result = json.loads(list_goals(tag="poka-1"))
    assert "db down" in result["error"]
    assert (log_calls[0][0], log_calls[0][3]) == ("list_goals", "error")


def test_get_goal_rolls_up_scheduled_backlog_and_direct_tasks(patched_get_session):
    """Mirrors GET /api/goals/{id}: tasks carrying ALL goal tags plus directly
    linked ones, whether scheduled or in the backlog, each listed once."""
    gid = json.loads(create_goal("Epic", tag_names=["poka-1", "team"]))["id"]
    add_backlog_task("Backlog child", tags=["POKA-1", "team"])
    create_task("Scheduled child", "deep_work", tags=["poka-1", "team"])
    add_backlog_task("Only one tag", tags=["poka-1"])  # AND semantics: excluded
    add_backlog_task("Direct", tags=[])
    add_backlog_task("Direct and tagged", tags=["poka-1", "team"])
    with patched_get_session() as session:
        goal = session.get(Goal, gid)
        for title in ("Direct", "Direct and tagged"):
            goal.direct_tasks.append(session.query(Task).filter_by(title=title).one())

    result = json.loads(get_goal(gid))
    tasks = {t["title"]: t for t in result["tasks"]}
    assert sorted(tasks) == [
        "Backlog child", "Direct", "Direct and tagged", "Scheduled child"
    ]
    assert tasks["Backlog child"]["day"] is None
    assert tasks["Scheduled child"]["day"] is not None
    assert result["title"] == "Epic"


def test_get_goal_lists_sub_goals_without_their_tasks(patched_get_session):
    """Like the endpoint, child goals are listed; their tasks are fetched per child."""
    parent = json.loads(create_goal("Parent"))["id"]
    child = json.loads(create_goal("Child", tag_names=["kid"]))["id"]
    with patched_get_session() as session:
        session.get(Goal, child).parent_goal_id = parent
    add_backlog_task("Kid task", tags=["kid"])

    result = json.loads(get_goal(parent))
    assert result["tasks"] == []
    assert [g["id"] for g in result["sub_goals"]] == [child]


def test_get_goal_unknown_id_is_error_and_logged(patched_get_session, log_calls):
    """A missing goal must be reported, not returned as an empty goal."""
    assert "error" in json.loads(get_goal(999))
    assert (log_calls[-1][0], log_calls[-1][3]) == ("get_goal", "error")
