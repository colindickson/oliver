"""Days-off tools: mark/unmark days as off and manage recurring configuration."""

import json
from datetime import date

from models.day import Day
from models.day_off import DayOff
from models.setting import Setting
from tools.daily import _get_or_create_day, get_session
from tools.log_utils import log_call

VALID_REASONS = frozenset(
    {"weekend", "personal_day", "vacation", "holiday", "sick_day"}
)

VALID_WEEKDAYS = frozenset(
    {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
)

RECURRING_DAYS_OFF_KEY = "recurring_days_off"


def mark_day_off(date_str: str, reason: str, note: str = "") -> str:
    """Mark a day as an off day with a given reason.

    Args:
        date_str: ISO-8601 date string (YYYY-MM-DD).
        reason: One of: weekend, personal_day, vacation, holiday, sick_day.
        note: Optional free-text context for the off day.

    Returns:
        JSON-encoded dict with ``success`` and the saved fields, or ``error``.
    """
    params = {"date_str": date_str, "reason": reason, "note": note}
    if reason not in VALID_REASONS:
        error_json = json.dumps(
            {"error": f"Invalid reason '{reason}'. Must be one of: {sorted(VALID_REASONS)}"}
        )
        log_call("mark_day_off", params, error_json, "error")
        return error_json

    try:
        target = date.fromisoformat(date_str)
    except ValueError:
        error_json = json.dumps({"error": f"Invalid date format '{date_str}'. Use YYYY-MM-DD."})
        log_call("mark_day_off", params, error_json, "error")
        return error_json

    try:
        with get_session() as session:
            day = _get_or_create_day(session, target)
            day_off = session.query(DayOff).filter(DayOff.day_id == day.id).first()
            if day_off:
                day_off.reason = reason
                day_off.note = note or None
            else:
                day_off = DayOff(
                    day_id=day.id,
                    reason=reason,
                    note=note or None,
                )
                session.add(day_off)

        result_json = json.dumps(
            {
                "success": True,
                "date": target.isoformat(),
                "reason": reason,
                "note": note or None,
            }
        )
        log_call("mark_day_off", params, result_json, "success", before_state=None)
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("mark_day_off", params, error_json, "error")
        return error_json


def unmark_day_off(date_str: str) -> str:
    """Remove the off-day designation for a given date (idempotent).

    Args:
        date_str: ISO-8601 date string (YYYY-MM-DD).

    Returns:
        JSON-encoded dict with ``success`` and ``date``, or ``error``.
    """
    params = {"date_str": date_str}
    try:
        target = date.fromisoformat(date_str)
    except ValueError:
        error_json = json.dumps({"error": f"Invalid date format '{date_str}'. Use YYYY-MM-DD."})
        log_call("unmark_day_off", params, error_json, "error")
        return error_json

    try:
        with get_session() as session:
            day = session.query(Day).filter(Day.date == target).first()
            before_state = None
            if day:
                day_off = session.query(DayOff).filter(DayOff.day_id == day.id).first()
                if day_off:
                    before_state = {
                        "day_date": target.isoformat(),
                        "reason": day_off.reason,
                        "note": day_off.note,
                    }
                    session.delete(day_off)

        result_json = json.dumps({"success": True, "date": target.isoformat()})
        log_call("unmark_day_off", params, result_json, "success", before_state=before_state)
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("unmark_day_off", params, error_json, "error")
        return error_json


def list_days_off() -> str:
    """Return all days marked as off.

    Returns:
        JSON-encoded dict with ``days`` array, each entry having ``date``,
        ``reason``, and ``note``.
    """
    params: dict = {}
    try:
        with get_session() as session:
            rows = (
                session.query(DayOff, Day.date)
                .join(Day, DayOff.day_id == Day.id)
                .order_by(Day.date.desc())
                .all()
            )
            entries = [
                {
                    "date": day_date.isoformat(),
                    "reason": day_off.reason,
                    "note": day_off.note,
                }
                for day_off, day_date in rows
            ]

        result_json = json.dumps({"days": entries}, indent=2)
        log_call("list_days_off", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("list_days_off", params, error_json, "error")
        return error_json


def is_day_off(date_str: str) -> str:
    """Check whether a given date is a day off.

    A date is considered a day off if its weekday appears in the recurring
    days-off setting, or if an explicit DayOff record exists for it.

    Args:
        date_str: ISO-8601 date string (YYYY-MM-DD).

    Returns:
        JSON-encoded dict with ``is_day_off`` bool, and optionally ``reason``
        and ``note``.  Returns ``error`` on invalid input.
    """
    params = {"date_str": date_str}
    try:
        target = date.fromisoformat(date_str)
    except ValueError:
        error_json = json.dumps({"error": f"Invalid date format: {date_str!r}. Use YYYY-MM-DD."})
        log_call("is_day_off", params, error_json, "error")
        return error_json

    weekday_name = target.strftime("%A").lower()

    try:
        with get_session() as session:
            setting = (
                session.query(Setting)
                .filter(Setting.key == RECURRING_DAYS_OFF_KEY)
                .first()
            )
            recurring = json.loads(setting.value) if setting else []
            if weekday_name in recurring:
                result_json = json.dumps({
                    "is_day_off": True,
                    "reason": "recurring",
                    "note": f"{weekday_name.capitalize()} is a recurring day off",
                })
                log_call("is_day_off", params, result_json, "success")
                return result_json

            day = session.query(Day).filter(Day.date == target).first()
            if day:
                day_off = session.query(DayOff).filter(DayOff.day_id == day.id).first()
                if day_off:
                    result_json = json.dumps({
                        "is_day_off": True,
                        "reason": day_off.reason,
                        "note": day_off.note,
                    })
                    log_call("is_day_off", params, result_json, "success")
                    return result_json

        result_json = json.dumps({"is_day_off": False})
        log_call("is_day_off", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("is_day_off", params, error_json, "error")
        return error_json


def get_recurring_days_off() -> str:
    """Return the configured recurring off weekdays from settings.

    Returns:
        JSON-encoded dict with ``days`` list of weekday name strings.
    """
    params: dict = {}
    try:
        with get_session() as session:
            setting = (
                session.query(Setting)
                .filter(Setting.key == RECURRING_DAYS_OFF_KEY)
                .first()
            )
            days = json.loads(setting.value) if setting else []

        result_json = json.dumps({"days": days})
        log_call("get_recurring_days_off", params, result_json, "success")
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("get_recurring_days_off", params, error_json, "error")
        return error_json


def set_recurring_days_off(days: list[str]) -> str:
    """Save the recurring off weekday names to settings.

    Args:
        days: List of lowercase weekday names
              (monday, tuesday, wednesday, thursday, friday, saturday, sunday).

    Returns:
        JSON-encoded dict with ``days`` list, or ``error`` for invalid names.
    """
    params = {"days": days}
    invalid = [d for d in days if d not in VALID_WEEKDAYS]
    if invalid:
        error_json = json.dumps(
            {
                "error": f"Invalid weekday name(s): {invalid}. "
                f"Must be one of: {sorted(VALID_WEEKDAYS)}"
            }
        )
        log_call("set_recurring_days_off", params, error_json, "error")
        return error_json

    try:
        with get_session() as session:
            setting = (
                session.query(Setting)
                .filter(Setting.key == RECURRING_DAYS_OFF_KEY)
                .first()
            )
            before_days = json.loads(setting.value) if setting else []
            before_state = {"days": before_days}
            if setting:
                setting.value = json.dumps(days)
            else:
                setting = Setting(key=RECURRING_DAYS_OFF_KEY, value=json.dumps(days))
                session.add(setting)

        result_json = json.dumps({"days": days})
        log_call("set_recurring_days_off", params, result_json, "success", before_state=before_state)
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("set_recurring_days_off", params, error_json, "error")
        return error_json
