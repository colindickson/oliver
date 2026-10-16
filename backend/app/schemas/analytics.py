"""Pydantic response schemas for the analytics endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    """Aggregated task completion statistics for a rolling time window.

    Attributes:
        period_days: The number of days the summary covers.
        total_days_tracked: Count of distinct Day records within the period.
        total_tasks: Total number of tasks across all days in the period.
        completed_tasks: Number of tasks with status ``completed``.
        completion_rate_pct: Percentage of tasks completed (0–100).
    """

    period_days: int
    total_days_tracked: int
    total_tasks: int
    completed_tasks: int
    completion_rate_pct: float


class StreaksResponse(BaseModel):
    """Consecutive-day completion streak metrics.

    Attributes:
        current_streak: Number of consecutive days ending today where every
            task was completed.
        longest_streak: Longest such consecutive run in the full history.
    """

    current_streak: int
    longest_streak: int


class WorkLogActivityDay(BaseModel):
    """Per-day work log activity summary for the bar chart.

    Attributes:
        date: ISO date string (YYYY-MM-DD).
        count: Total number of work log entries on this day.
        commit: Count of commit-type logs.
        pr: Count of pr-type logs.
        review: Count of review-type logs.
        research: Count of research-type logs.
        untyped: Count of logs with no log_type set.
    """

    date: str
    count: int
    commit: int
    pr: int
    review: int
    research: int
    untyped: int
