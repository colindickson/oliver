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


class CategoryTimeEntry(BaseModel):
    """Time-tracking summary for a single task category.

    Attributes:
        category: The task category label (e.g. ``deep_work``).
        total_seconds: Sum of ``duration_seconds`` across all timer sessions
            for tasks in this category.
        task_count: Number of distinct tasks that have timer sessions in this
            category.
    """

    category: str
    total_seconds: int
    task_count: int


class CategoriesResponse(BaseModel):
    """Wrapper for the list of per-category time entries.

    Attributes:
        entries: One entry per category that has recorded timer sessions.
    """

    entries: list[CategoryTimeEntry]


class TodayDeepWorkResponse(BaseModel):
    """Today's deep work time tracking progress.

    Attributes:
        total_seconds: Sum of all deep_work timer session durations for today.
        goal_seconds: The daily goal in seconds (3 hours = 10800 seconds).
    """

    total_seconds: int
    goal_seconds: int
