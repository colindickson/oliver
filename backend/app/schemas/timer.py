"""Pydantic schemas for Timer request and response payloads."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TimerStart(BaseModel):
    """Payload required to start or resume a timer.

    Attributes:
        task_id: The primary key of the Task to time.
    """

    task_id: int


class TimerAddTime(BaseModel):
    """Payload for manually adding time to a task.

    Attributes:
        task_id: The primary key of the Task to credit time to.
        seconds: Number of seconds to add (must be positive).
    """

    task_id: int
    seconds: int = Field(gt=0)


class TimerState(BaseModel):
    """Current timer state returned by GET /api/timer/current.

    Attributes:
        status: One of ``idle``, ``running``, or ``paused``.
        task_id: The task being timed; ``None`` when status is ``idle``.
        elapsed_seconds: Total seconds elapsed including any running interval.
        accumulated_seconds: Seconds accumulated from completed intervals only.
    """

    status: str  # "idle" | "running" | "paused"
    task_id: int | None = None
    elapsed_seconds: int = 0
    accumulated_seconds: int = 0


class TimerSessionResponse(BaseModel):
    """Serialised representation of a completed TimerSession.

    Attributes:
        id: Primary key.
        task_id: Foreign key to the timed Task.
        started_at: UTC timestamp when the timer interval began.
        ended_at: UTC timestamp when the timer was stopped.
        duration_seconds: Total duration of the session in seconds.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None
