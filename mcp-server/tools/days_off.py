"""Days-off tools: mark/unmark days as off and manage recurring configuration."""

import json
from datetime import date

from models.day import Day
from models.day_off import DayOff
from models.setting import Setting
from tools.daily import _get_or_create_day, get_session

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
    if reason not in VALID_REASONS:
        return json.dumps(
            {"error": f"Invalid reason '{reason}'. Must be one of: {sorted(VALID_REASONS)}"}
        )

    try:
        target = date.fromisoformat(date_str)
    except ValueError:
        return json.dumps({"error": f"Invalid date format '{date_str}'. Use YYYY-MM-DD."})

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

    return json.dumps(
        {
            "success": True,
            "date": target.isoformat(),
            "reason": reason,
            "note": note or None,
        }
    )


def unmark_day_off(date_str: str) -> str:
    """Remove the off-day designation for a given date (idempotent).

    Args:
        date_str: ISO-8601 date string (YYYY-MM-DD).

    Returns:
        JSON-encoded dict with ``success`` and ``date``, or ``error``.
    """
    try:
        target = date.fromisoformat(date_str)
    except ValueError:
        return json.dumps({"error": f"Invalid date format '{date_str}'. Use YYYY-MM-DD."})

    with get_session() as session:
        day = session.query(Day).filter(Day.date == target).first()
        if day:
            day_off = session.query(DayOff).filter(DayOff.day_id == day.id).first()
            if day_off:
                session.delete(day_off)

    return json.dumps({"success": True, "date": target.isoformat()})


def list_days_off() -> str:
    """Return all days marked as off.

    Returns:
        JSON-encoded dict with ``days`` array, each entry having ``date``,
        ``reason``, and ``note``.
    """
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

    return json.dumps({"days": entries}, indent=2)


def get_recurring_days_off() -> str:
    """Return the configured recurring off weekdays from settings.

    Returns:
        JSON-encoded dict with ``days`` list of weekday name strings.
    """
    with get_session() as session:
        setting = (
            session.query(Setting)
            .filter(Setting.key == RECURRING_DAYS_OFF_KEY)
            .first()
        )
        days = json.loads(setting.value) if setting else []

    return json.dumps({"days": days})


def set_recurring_days_off(days: list[str]) -> str:
    """Save the recurring off weekday names to settings.

    Args:
        days: List of lowercase weekday names
              (monday, tuesday, wednesday, thursday, friday, saturday, sunday).

    Returns:
        JSON-encoded dict with ``days`` list, or ``error`` for invalid names.
    """
    invalid = [d for d in days if d not in VALID_WEEKDAYS]
    if invalid:
        return json.dumps(
            {
                "error": f"Invalid weekday name(s): {invalid}. "
                f"Must be one of: {sorted(VALID_WEEKDAYS)}"
            }
        )

    with get_session() as session:
        setting = (
            session.query(Setting)
            .filter(Setting.key == RECURRING_DAYS_OFF_KEY)
            .first()
        )
        if setting:
            setting.value = json.dumps(days)
        else:
            setting = Setting(key=RECURRING_DAYS_OFF_KEY, value=json.dumps(days))
            session.add(setting)

    return json.dumps({"days": days})
