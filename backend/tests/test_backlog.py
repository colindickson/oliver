"""Tests for the /api/backlog endpoints.

Written before the implementation exists (TDD red phase).

The backlog is idle work: unfinished tasks with no day or on any day other
than today, that have not already been continued.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Day, Goal, Tag, Task
from app.models.task import (
    CATEGORY_DEEP_WORK,
    CATEGORY_SHORT_TASK,
    STATUS_PENDING,
)


@pytest.fixture
async def day(db_session: AsyncSession) -> Day:
    """Insert a Day record and return it for use in tests."""
    d = Day(date=date(2025, 6, 1), created_at=datetime.now(timezone.utc))
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


async def _make_day(db: AsyncSession, d: date) -> Day:
    day = Day(date=d, created_at=datetime.now(timezone.utc))
    db.add(day)
    await db.commit()
    await db.refresh(day)
    return day


@pytest.fixture
async def today_day(db_session: AsyncSession) -> Day:
    return await _make_day(db_session, date.today())


@pytest.fixture
async def future_day(db_session: AsyncSession) -> Day:
    return await _make_day(db_session, date.today() + timedelta(days=3))


async def _make_task(
    db: AsyncSession, day_id: int | None, title: str = "T", status: str = STATUS_PENDING, **kw
) -> Task:
    t = Task(
        day_id=day_id,
        category=kw.pop("category", CATEGORY_DEEP_WORK),
        title=title,
        status=status,
        order_index=0,
        **kw,
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


# ---------------------------------------------------------------------------
# GET /api/backlog - list backlog tasks
# ---------------------------------------------------------------------------


async def test_list_backlog_returns_only_backlog_tasks(
    client: AsyncClient, today_day: Day
) -> None:
    """A task being worked on today is not idle, so it stays out of the backlog."""
    # Create a backlog task (day_id not provided)
    await client.post(
        "/api/backlog",
        json={"title": "Backlog task"},
    )

    # Create a regular day task
    await client.post(
        "/api/tasks",
        json={"day_id": today_day.id, "category": CATEGORY_DEEP_WORK, "title": "Day task"},
    )

    response = await client.get("/api/backlog")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Backlog task"
    assert body[0]["day_id"] is None


async def test_list_backlog_with_tag_filter(client: AsyncClient) -> None:
    """GET /api/backlog?tag=xyz filters by tag name."""
    # Create backlog tasks with different tags
    await client.post(
        "/api/backlog",
        json={"title": "Task with focus tag", "tags": ["focus"]},
    )
    await client.post(
        "/api/backlog",
        json={"title": "Task with other tag", "tags": ["other"]},
    )

    response = await client.get("/api/backlog?tag=focus")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Task with focus tag"
    assert body[0]["tags"] == ["focus"]


async def test_list_backlog_with_search(client: AsyncClient) -> None:
    """GET /api/backlog?search=xyz filters by title substring."""
    await client.post(
        "/api/backlog",
        json={"title": "Important project"},
    )
    await client.post(
        "/api/backlog",
        json={"title": "Random idea"},
    )

    response = await client.get("/api/backlog?search=project")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Important project"


async def test_list_backlog_returns_empty_list_when_no_tasks(
    client: AsyncClient,
) -> None:
    """GET /api/backlog returns [] when no backlog tasks exist."""
    response = await client.get("/api/backlog")

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# POST /api/backlog - create backlog task
# ---------------------------------------------------------------------------


async def test_create_backlog_task(client: AsyncClient) -> None:
    """POST /api/backlog creates a task with day_id=None and category=None."""
    payload = {
        "title": "Future task",
        "description": "Something to do later",
    }
    response = await client.post("/api/backlog", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Future task"
    assert body["description"] == "Something to do later"
    assert body["day_id"] is None
    assert body["category"] is None
    assert body["status"] == STATUS_PENDING
    assert body["order_index"] == 0
    assert body["completed_at"] is None
    assert "id" in body
    assert body["tags"] == []


async def test_create_backlog_task_with_category(client: AsyncClient) -> None:
    """POST /api/backlog creates a task with an optional suggested category."""
    payload = {
        "title": "Suggested deep work",
        "suggested_category": CATEGORY_DEEP_WORK,
    }
    response = await client.post("/api/backlog", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Suggested deep work"
    # Category should be stored as suggested_category
    assert body["category"] == CATEGORY_DEEP_WORK


async def test_create_backlog_task_with_tags(client: AsyncClient) -> None:
    """POST /api/backlog creates a task with tags."""
    payload = {
        "title": "Tagged backlog task",
        "tags": ["focus", "project-x"],
    }
    response = await client.post("/api/backlog", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Tagged backlog task"
    assert set(body["tags"]) == {"focus", "project-x"}


# ---------------------------------------------------------------------------
# POST /api/backlog/{id}/move-to-day - move backlog task to a day
# ---------------------------------------------------------------------------


async def test_move_backlog_task_to_day(client: AsyncClient, day: Day) -> None:
    """POST /api/backlog/{id}/move-to-day moves task from backlog to a day."""
    # Create a backlog task
    create_resp = await client.post(
        "/api/backlog",
        json={"title": "Task to move"},
    )
    task_id = create_resp.json()["id"]

    # Move to day
    move_resp = await client.post(
        f"/api/backlog/{task_id}/move-to-day",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK},
    )

    assert move_resp.status_code == 200
    body = move_resp.json()
    assert body["day_id"] == day.id
    assert body["category"] == CATEGORY_DEEP_WORK
    assert body["title"] == "Task to move"


async def test_move_backlog_task_to_day_uses_existing_category(
    client: AsyncClient, day: Day
) -> None:
    """POST /api/backlog/{id}/move-to-day uses existing category if not provided."""
    # Create a backlog task with a suggested category
    create_resp = await client.post(
        "/api/backlog",
        json={"title": "Pre-categorized task", "suggested_category": CATEGORY_SHORT_TASK},
    )
    task_id = create_resp.json()["id"]

    # Move to day without specifying category
    move_resp = await client.post(
        f"/api/backlog/{task_id}/move-to-day",
        json={"day_id": day.id},
    )

    assert move_resp.status_code == 200
    body = move_resp.json()
    assert body["day_id"] == day.id
    assert body["category"] == CATEGORY_SHORT_TASK


async def test_move_backlog_task_to_day_returns_404_for_nonexistent_task(
    client: AsyncClient, day: Day
) -> None:
    """POST /api/backlog/{id}/move-to-day returns 404 for non-existent task."""
    response = await client.post(
        "/api/backlog/99999/move-to-day",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK},
    )

    assert response.status_code == 404


async def test_move_backlog_task_to_day_removes_from_backlog_list(
    client: AsyncClient, today_day: Day
) -> None:
    """Scheduling onto today removes the task from the backlog (a past day would not)."""
    # Create a backlog task
    create_resp = await client.post(
        "/api/backlog",
        json={"title": "Task to move"},
    )
    task_id = create_resp.json()["id"]

    # Verify it appears in backlog
    list_resp = await client.get("/api/backlog")
    assert len(list_resp.json()) == 1

    # Move to day
    await client.post(
        f"/api/backlog/{task_id}/move-to-day",
        json={"day_id": today_day.id, "category": CATEGORY_DEEP_WORK},
    )

    # Verify it no longer appears in backlog
    list_resp = await client.get("/api/backlog")
    assert len(list_resp.json()) == 0


# ---------------------------------------------------------------------------
# POST /api/tasks/{id}/move-to-backlog - move task to backlog
# ---------------------------------------------------------------------------


async def test_move_task_to_backlog(client: AsyncClient, day: Day) -> None:
    """POST /api/tasks/{id}/move-to-backlog moves task from day to backlog."""
    # Create a regular day task
    create_resp = await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "Day task"},
    )
    task_id = create_resp.json()["id"]

    # Move to backlog
    move_resp = await client.post(f"/api/tasks/{task_id}/move-to-backlog")

    assert move_resp.status_code == 200
    body = move_resp.json()
    assert body["day_id"] is None
    assert body["category"] is None
    assert body["title"] == "Day task"


async def test_move_task_to_backlog_returns_404(client: AsyncClient) -> None:
    """POST /api/tasks/{id}/move-to-backlog returns 404 for non-existent task."""
    response = await client.post("/api/tasks/99999/move-to-backlog")

    assert response.status_code == 404


async def test_move_task_to_backlog_appears_in_backlog_list(
    client: AsyncClient, today_day: Day
) -> None:
    """Moving a task off today to the backlog makes it appear in the backlog list."""
    # Create a regular day task
    create_resp = await client.post(
        "/api/tasks",
        json={"day_id": today_day.id, "category": CATEGORY_DEEP_WORK, "title": "Day task"},
    )
    task_id = create_resp.json()["id"]

    # Verify backlog is empty
    list_resp = await client.get("/api/backlog")
    assert len(list_resp.json()) == 0

    # Move to backlog
    await client.post(f"/api/tasks/{task_id}/move-to-backlog")

    # Verify it now appears in backlog
    list_resp = await client.get("/api/backlog")
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["title"] == "Day task"


async def test_move_task_to_backlog_preserves_tags(client: AsyncClient, day: Day) -> None:
    """Moving a task to backlog preserves its tags."""
    # Create a task with tags
    create_resp = await client.post(
        "/api/tasks",
        json={
            "day_id": day.id,
            "category": CATEGORY_DEEP_WORK,
            "title": "Tagged task",
            "tags": ["focus", "project"],
        },
    )
    task_id = create_resp.json()["id"]

    # Move to backlog
    move_resp = await client.post(f"/api/tasks/{task_id}/move-to-backlog")

    assert move_resp.status_code == 200
    body = move_resp.json()
    assert set(body["tags"]) == {"focus", "project"}


# ---------------------------------------------------------------------------
# Backlog = idle work (derived, not a day_id IS NULL flag)
# ---------------------------------------------------------------------------


async def test_unfinished_goal_task_on_past_day_is_in_backlog(
    client: AsyncClient, db_session: AsyncSession, day: Day
) -> None:
    """The user's literal complaint: an unfinished goal task left on a past day
    must show up in the backlog with no manual action."""
    t = await _make_task(db_session, day.id, "Stale goal task")
    resp = await client.post("/api/goals", json={"title": "G", "task_ids": [t.id]})
    assert resp.status_code == 201

    body = (await client.get("/api/backlog")).json()

    assert [b["id"] for b in body] == [t.id]


async def test_backlog_exclusion_matrix(
    client: AsyncClient,
    db_session: AsyncSession,
    day: Day,
    today_day: Day,
    future_day: Day,
) -> None:
    """Each case fails if the idle predicate is loosened; the last (an original
    that already has a continuation) replaces a data migration for the 129/162 shape."""
    await _make_task(db_session, today_day.id, "on today")
    await _make_task(db_session, day.id, "done past", status="completed")
    await _make_task(db_session, None, "done dayless", status="completed")
    await _make_task(db_session, day.id, "rolled", status="rolled_forward")
    orig = await _make_task(db_session, day.id, "continued original")
    cont = await _make_task(db_session, today_day.id, "continuation", rolled_from_task_id=orig.id)
    idle_dayless = await _make_task(db_session, None, "idle dayless")
    idle_past = await _make_task(db_session, day.id, "idle past", status="in_progress")
    idle_future = await _make_task(db_session, future_day.id, "idle future")

    body = (await client.get("/api/backlog")).json()

    assert {b["id"] for b in body} == {idle_dayless.id, idle_past.id, idle_future.id}
    assert cont.id not in {b["id"] for b in body}


async def test_backlog_day_date_and_ordering(
    client: AsyncClient,
    db_session: AsyncSession,
    day: Day,
    future_day: Day,
) -> None:
    """Pickers show 'from {date}' / 'on {date}' from day_date; ordering is
    day-less, then past most-recent-first, then future soonest-first."""
    older = await _make_day(db_session, date(2025, 5, 1))
    later_future = await _make_day(db_session, date.today() + timedelta(days=9))
    f2 = await _make_task(db_session, later_future.id, "f2")
    f1 = await _make_task(db_session, future_day.id, "f1")
    p_old = await _make_task(db_session, older.id, "p_old")
    p_new = await _make_task(db_session, day.id, "p_new")
    nod = await _make_task(db_session, None, "nod")

    body = (await client.get("/api/backlog")).json()

    assert [b["id"] for b in body] == [nod.id, p_new.id, p_old.id, f1.id, f2.id]
    assert body[0]["day_date"] is None
    assert body[1]["day_date"] == "2025-06-01"
    assert body[3]["day_date"] == future_day.date.isoformat()


async def test_backlog_tag_filter_does_not_duplicate_rows(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A task with several tags must appear once when filtering by one tag."""
    await client.post("/api/backlog", json={"title": "multi", "tags": ["a", "b"]})

    body = (await client.get("/api/backlog?tag=a")).json()

    assert len(body) == 1


async def test_pick_past_day_task_rolls_forward(
    client: AsyncClient, db_session: AsyncSession, day: Day, today_day: Day
) -> None:
    """History is kept: the original stays on its past day as rolled_forward and a
    copy lands on the target day, so nothing is duplicated in the backlog."""
    created = await client.post(
        "/api/tasks",
        json={"day_id": day.id, "category": CATEGORY_DEEP_WORK, "title": "stale", "tags": ["t1"]},
    )
    orig_id = created.json()["id"]

    r = await client.post(f"/api/backlog/{orig_id}/move-to-day", json={"day_id": today_day.id})

    assert r.status_code == 200
    body = r.json()
    assert body["id"] != orig_id
    assert body["day_id"] == today_day.id
    assert body["rolled_from_task_id"] == orig_id
    assert body["rolled_from_date"] == "2025-06-01"
    assert body["tags"] == ["t1"]
    assert body["category"] == CATEGORY_DEEP_WORK
    assert body["status"] == STATUS_PENDING
    original = await db_session.get(Task, orig_id)
    await db_session.refresh(original)
    assert original.day_id == day.id
    assert original.status == "rolled_forward"
    ids = {b["id"] for b in (await client.get("/api/backlog")).json()}
    assert orig_id not in ids and body["id"] not in ids


async def test_pick_resets_in_progress_copy_to_pending(
    client: AsyncClient, db_session: AsyncSession, day: Day, today_day: Day
) -> None:
    """A stale in_progress task has no live timer state on its copy: reset to pending."""
    t = await _make_task(db_session, day.id, "ip", status="in_progress")

    r = await client.post(f"/api/backlog/{t.id}/move-to-day", json={"day_id": today_day.id})

    assert r.json()["status"] == STATUS_PENDING


async def test_rolled_forward_copy_keeps_goal_membership(
    client: AsyncClient, db_session: AsyncSession, day: Day, today_day: Day
) -> None:
    """Goal membership must survive the id change: the copy rolls up, the original
    is excluded from detail, and progress total is unchanged."""
    t = await _make_task(db_session, day.id, "goal task")
    g = (await client.post("/api/goals", json={"title": "G", "task_ids": [t.id]})).json()

    r = await client.post(f"/api/backlog/{t.id}/move-to-day", json={"day_id": today_day.id})
    new_id = r.json()["id"]

    detail = (await client.get(f"/api/goals/{g['id']}")).json()
    assert [x["id"] for x in detail["tasks"]] == [new_id]
    assert detail["total_tasks"] == 1


async def test_pick_past_task_keeps_completion_rate_and_streak(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Why we roll forward instead of moving the row: moving a pending task off a
    past day would make that day look fully complete and rewrite analytics history."""
    d = date.today() - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    past = await _make_day(db_session, d)
    today = await _make_day(db_session, date.today())
    await _make_task(db_session, past.id, "done", status="completed")
    pending = await _make_task(db_session, past.id, "pending")
    before = (await client.get("/api/analytics/summary")).json()["completion_rate_pct"]
    assert (await client.get("/api/analytics/streaks")).json()["current_streak"] == 0

    r = await client.post(f"/api/backlog/{pending.id}/move-to-day", json={"day_id": today.id})
    assert r.status_code == 200

    after = (await client.get("/api/analytics/summary")).json()["completion_rate_pct"]
    assert after == before
    assert (await client.get("/api/analytics/streaks")).json()["current_streak"] == 0


async def test_pick_dayless_or_future_task_keeps_id(
    client: AsyncClient, db_session: AsyncSession, today_day: Day, future_day: Day
) -> None:
    """Day-less and future tasks are moved, not copied: same id, so tags, links and
    timer sessions stay, and the delete-orphan relationship is never touched."""
    nod = await _make_task(db_session, None, "nod")
    fut = await _make_task(db_session, future_day.id, "fut")

    for t in (nod, fut):
        r = await client.post(f"/api/backlog/{t.id}/move-to-day", json={"day_id": today_day.id})
        assert r.status_code == 200
        assert r.json()["id"] == t.id
        assert r.json()["day_id"] == today_day.id


async def test_pick_task_already_on_target_day_is_unchanged(
    client: AsyncClient, db_session: AsyncSession, today_day: Day
) -> None:
    """Re-picking onto the same day must not create a copy."""
    t = await _make_task(db_session, today_day.id, "here")

    r = await client.post(f"/api/backlog/{t.id}/move-to-day", json={"day_id": today_day.id})

    assert r.status_code == 200
    assert r.json()["id"] == t.id


async def test_pick_completed_or_continued_task_is_422(
    client: AsyncClient, db_session: AsyncSession, day: Day, today_day: Day
) -> None:
    """Terminal tasks and ones with a continuation must not be duplicated again."""
    done = await _make_task(db_session, day.id, "done", status="completed")
    orig = await _make_task(db_session, day.id, "orig")
    await _make_task(db_session, today_day.id, "cont", rolled_from_task_id=orig.id)

    for t in (done, orig):
        r = await client.post(f"/api/backlog/{t.id}/move-to-day", json={"day_id": today_day.id})
        assert r.status_code == 422


async def test_pick_past_task_onto_past_day_is_400(
    client: AsyncClient, db_session: AsyncSession, day: Day
) -> None:
    """A rolled-forward copy on a past day would just be idle again."""
    other = await _make_day(db_session, date(2025, 5, 1))
    t = await _make_task(db_session, day.id, "stale")

    r = await client.post(f"/api/backlog/{t.id}/move-to-day", json={"day_id": other.id})

    assert r.status_code == 400


async def test_pick_unknown_task_or_day_is_404(
    client: AsyncClient, db_session: AsyncSession, today_day: Day
) -> None:
    t = await _make_task(db_session, None, "nod")
    assert (
        await client.post("/api/backlog/99999/move-to-day", json={"day_id": today_day.id})
    ).status_code == 404
    assert (
        await client.post(f"/api/backlog/{t.id}/move-to-day", json={"day_id": 99999})
    ).status_code == 404


async def test_pick_without_resolvable_category_is_400(
    client: AsyncClient, db_session: AsyncSession, today_day: Day
) -> None:
    """A day slot needs a category; neither body nor task supplies one."""
    t = await _make_task(db_session, None, "nocat", category=None)

    r = await client.post(f"/api/backlog/{t.id}/move-to-day", json={"day_id": today_day.id})

    assert r.status_code == 400


async def test_roll_forward_repoints_running_timer_to_the_copy(
    client: AsyncClient, db_session: AsyncSession, day: Day, today_day: Day
) -> None:
    """Rolling a past-day task forward replaces its id; a running timer left on
    the old (now rolled_forward) id would stop crediting the work the user is
    actually doing, so the timer must follow the copy without losing time."""
    from app.services.timer_service import TimerService

    orig = await _make_task(db_session, day.id, "timed")
    timer = TimerService(db_session)
    await timer.start(orig.id)
    await db_session.commit()
    before, version_before = await timer._get_state()

    r = await client.post(f"/api/backlog/{orig.id}/move-to-day", json={"day_id": today_day.id})
    new_id = r.json()["id"]

    after, version_after = await timer._get_state()
    assert after["task_id"] == new_id
    assert after["status"] == "running"
    assert after["started_at"] == before["started_at"]
    assert after["accumulated_seconds"] == before["accumulated_seconds"]
    assert version_after > version_before


async def test_roll_forward_repoints_paused_timer_keeping_accumulated(
    client: AsyncClient, db_session: AsyncSession, day: Day, today_day: Day
) -> None:
    """A paused timer's accumulated time belongs to the work, not the row id."""
    from app.services.timer_service import TimerService

    orig = await _make_task(db_session, day.id, "paused")
    timer = TimerService(db_session)
    await timer.start(orig.id)
    await timer.add_time(orig.id, 120)
    await timer.pause()
    await db_session.commit()

    r = await client.post(f"/api/backlog/{orig.id}/move-to-day", json={"day_id": today_day.id})

    current = await timer.get_current()
    assert current["task_id"] == r.json()["id"]
    assert current["status"] == "paused"
    assert current["accumulated_seconds"] >= 120


async def test_roll_forward_leaves_timer_on_other_task_alone(
    client: AsyncClient, db_session: AsyncSession, day: Day, today_day: Day
) -> None:
    """Only a timer on the rolled task may move; someone else's timer must not."""
    from app.services.timer_service import TimerService

    orig = await _make_task(db_session, day.id, "rolled")
    other = await _make_task(db_session, today_day.id, "other")
    timer = TimerService(db_session)
    await timer.start(other.id)
    await db_session.commit()

    await client.post(f"/api/backlog/{orig.id}/move-to-day", json={"day_id": today_day.id})

    assert (await timer.get_current())["task_id"] == other.id
