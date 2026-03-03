"""Timer tools: start, stop, and persist focused-work intervals."""

import json
from datetime import datetime, timezone

from models.setting import Setting
from models.timer_session import TimerSession
from tools.daily import get_session
from tools.log_utils import log_call

# Settings table key used to persist the active timer state across MCP calls.
_TIMER_KEY = "active_timer"


def _get_timer_state(session) -> dict | None:
    """Read the active timer state from the settings table.

    Args:
        session: An active SQLAlchemy session.

    Returns:
        Parsed timer state dict, or ``None`` when no timer is stored.
    """
    row = session.query(Setting).filter(Setting.key == _TIMER_KEY).first()
    return json.loads(row.value) if row is not None else None


def _set_timer_state(session, state: dict) -> None:
    """Persist *state* to the settings table, upserting as needed.

    Args:
        session: An active SQLAlchemy session.
        state: Timer state dict to serialise and store.
    """
    row = session.query(Setting).filter(Setting.key == _TIMER_KEY).first()
    if row is None:
        session.add(Setting(key=_TIMER_KEY, value=json.dumps(state)))
    else:
        row.value = json.dumps(state)


def _clear_timer_state(session) -> None:
    """Remove the active timer state from the settings table.

    Args:
        session: An active SQLAlchemy session.
    """
    row = session.query(Setting).filter(Setting.key == _TIMER_KEY).first()
    if row is not None:
        session.delete(row)


def start_timer(task_id: int) -> str:
    """Start the timer for a task, resuming accumulated time if paused on the same task.

    Rejects the request when a timer is already running on any task.

    Args:
        task_id: Primary key of the task to time.

    Returns:
        JSON-encoded dict with ``success``, ``task_id``, and ``status``, or an
        ``error`` key when a timer is already running.
    """
    params = {"task_id": task_id}
    try:
        with get_session() as session:
            state = _get_timer_state(session)
            before_state = {"active_timer": state}
            if state and state["status"] == "running":
                error_json = json.dumps({"error": "Timer already running"})
                log_call("start_timer", params, error_json, "error")
                return error_json
            now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            # Carry forward accumulated seconds only when resuming the same task.
            accumulated = (
                state.get("accumulated_seconds", 0)
                if state and state.get("task_id") == task_id
                else 0
            )
            _set_timer_state(
                session,
                {
                    "task_id": task_id,
                    "status": "running",
                    "started_at": now,
                    "accumulated_seconds": accumulated,
                },
            )

        result_json = json.dumps({"success": True, "task_id": task_id, "status": "running"})
        log_call("start_timer", params, result_json, "success", before_state=before_state)
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("start_timer", params, error_json, "error")
        return error_json


def stop_timer(task_id: int) -> str:
    """Stop the running timer and persist a TimerSession record.

    Calculates the elapsed wall-clock seconds since ``started_at``, adds any
    previously accumulated seconds (from paused intervals), and writes a
    ``TimerSession`` row. The active timer state is then cleared.

    Args:
        task_id: Primary key of the task whose timer should be stopped.

    Returns:
        JSON-encoded dict with ``success`` and ``duration_seconds``, or an
        ``error`` key when no timer is active.
    """
    params = {"task_id": task_id}
    try:
        with get_session() as session:
            state = _get_timer_state(session)
            if not state:
                error_json = json.dumps({"error": "No timer running"})
                log_call("stop_timer", params, error_json, "error")
                return error_json

            before_state = {"active_timer": state, "timer_session_id": None}

            now = datetime.now(timezone.utc).replace(tzinfo=None)
            accumulated = state.get("accumulated_seconds", 0)
            if state["status"] == "running":
                started_at = datetime.fromisoformat(state["started_at"])
                total = accumulated + int((now - started_at).total_seconds())
            else:
                total = accumulated
            ts = TimerSession(
                task_id=state["task_id"],
                started_at=datetime.fromisoformat(state["started_at"]),
                ended_at=now,
                duration_seconds=total,
            )
            session.add(ts)
            session.flush()
            timer_session_id = ts.id
            _clear_timer_state(session)

        result_json = json.dumps({"success": True, "duration_seconds": total,
                                  "timer_session_id": timer_session_id})
        log_call("stop_timer", params, result_json, "success", before_state=before_state)
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("stop_timer", params, error_json, "error")
        return error_json
