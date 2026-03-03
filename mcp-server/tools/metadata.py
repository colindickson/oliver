"""Metadata tool: set weather and moon-phase context for a given date."""

import json
from datetime import date

from models.day_metadata import DayMetadata
from tools.daily import _get_or_create_day, get_session
from tools.log_utils import log_call

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
    params = {"date_str": date_str, "temperature_c": temperature_c,
              "condition": condition, "moon_phase": moon_phase}
    if condition is not None and condition not in VALID_CONDITIONS:
        error_json = json.dumps(
            {"error": f"Invalid condition '{condition}'. Must be one of: {sorted(VALID_CONDITIONS)}"}
        )
        log_call("set_day_metadata", params, error_json, "error")
        return error_json

    if moon_phase is not None and moon_phase not in VALID_MOON_PHASES:
        error_json = json.dumps(
            {"error": f"Invalid moon_phase '{moon_phase}'. Must be one of: {sorted(VALID_MOON_PHASES)}"}
        )
        log_call("set_day_metadata", params, error_json, "error")
        return error_json

    try:
        target = date.fromisoformat(date_str)
    except ValueError:
        error_json = json.dumps({"error": f"Invalid date format '{date_str}'. Use YYYY-MM-DD."})
        log_call("set_day_metadata", params, error_json, "error")
        return error_json

    try:
        with get_session() as session:
            day = _get_or_create_day(session, target)
            meta = session.query(DayMetadata).filter(DayMetadata.day_id == day.id).first()
            if meta:
                before_state = {
                    "temperature_c": meta.temperature_c,
                    "condition": meta.condition,
                    "moon_phase": meta.moon_phase,
                }
                meta.temperature_c = temperature_c
                meta.condition = condition
                meta.moon_phase = moon_phase
            else:
                before_state = None
                meta = DayMetadata(
                    day_id=day.id,
                    temperature_c=temperature_c,
                    condition=condition,
                    moon_phase=moon_phase,
                )
                session.add(meta)

        result_json = json.dumps(
            {
                "success": True,
                "date": target.isoformat(),
                "temperature_c": temperature_c,
                "condition": condition,
                "moon_phase": moon_phase,
            }
        )
        log_call("set_day_metadata", params, result_json, "success", before_state=before_state)
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("set_day_metadata", params, error_json, "error")
        return error_json
