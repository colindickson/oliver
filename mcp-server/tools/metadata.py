"""Metadata tool: set weather and moon-phase context for a given date."""

import json
from datetime import date

from models.day_metadata import DayMetadata
from tools.daily import _get_or_create_day, get_session

VALID_CONDITIONS = frozenset(
    {"sunny", "partly_cloudy", "cloudy", "rainy", "snowy", "stormy", "foggy"}
)

VALID_MOON_PHASES = frozenset(
    {
        "new_moon", "waxing_crescent", "first_quarter", "waxing_gibbous",
        "full_moon", "waning_gibbous", "last_quarter", "waning_crescent",
    }
)


def set_day_metadata(
    date_str: str,
    temperature_c: float | None = None,
    condition: str | None = None,
    moon_phase: str | None = None,
) -> str:
    """Create or update environmental metadata for a given day.

    Args:
        date_str: ISO-8601 date string (YYYY-MM-DD).
        temperature_c: Temperature in Celsius, or None to clear.
        condition: Weather condition string (must be a valid value), or None.
        moon_phase: Moon phase string (must be a valid value), or None.

    Returns:
        JSON-encoded dict with ``success`` and the saved fields, or ``error``.
    """
    if condition is not None and condition not in VALID_CONDITIONS:
        return json.dumps(
            {"error": f"Invalid condition '{condition}'. Must be one of: {sorted(VALID_CONDITIONS)}"}
        )

    if moon_phase is not None and moon_phase not in VALID_MOON_PHASES:
        return json.dumps(
            {"error": f"Invalid moon_phase '{moon_phase}'. Must be one of: {sorted(VALID_MOON_PHASES)}"}
        )

    try:
        target = date.fromisoformat(date_str)
    except ValueError:
        return json.dumps({"error": f"Invalid date format '{date_str}'. Use YYYY-MM-DD."})

    with get_session() as session:
        day = _get_or_create_day(session, target)
        meta = session.query(DayMetadata).filter(DayMetadata.day_id == day.id).first()
        if meta:
            meta.temperature_c = temperature_c
            meta.condition = condition
            meta.moon_phase = moon_phase
        else:
            meta = DayMetadata(
                day_id=day.id,
                temperature_c=temperature_c,
                condition=condition,
                moon_phase=moon_phase,
            )
            session.add(meta)

    return json.dumps(
        {
            "success": True,
            "date": target.isoformat(),
            "temperature_c": temperature_c,
            "condition": condition,
            "moon_phase": moon_phase,
        }
    )
