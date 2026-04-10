"""Pydantic schemas for Goal request and response payloads."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas._shared import TagCoercionMixin
from app.schemas.task import TaskResponse


class GoalCreate(BaseModel):
    """Payload required to create a new Goal."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    target_date: date | None = None
    tag_names: list[str] = []
    task_ids: list[int] = []


class GoalUpdate(BaseModel):
    """Payload for partial updates to a Goal.

    Pass ``target_date="CLEAR"`` to remove the target date.
    Otherwise, pass an ISO date string (YYYY-MM-DD).
    """

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    target_date: str | None = None  # ISO date string, or "CLEAR" sentinel
    tag_names: list[str] | None = None
    task_ids: list[int] | None = None

    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v == "CLEAR":
            return v
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(
                f"target_date must be a valid ISO date (YYYY-MM-DD) or 'CLEAR', got '{v}'"
            )
        return v


class GoalStatusUpdate(BaseModel):
    """Payload for changing a Goal's status."""

    status: Literal["active", "completed"]


class GoalResponse(TagCoercionMixin):
    """Serialised representation of a Goal returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    target_date: date | None
    status: str
    completed_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    tags: list[str]
    total_tasks: int
    completed_tasks: int
    progress_pct: int  # 0-100


class GoalDetailResponse(GoalResponse):
    """Goal response with full task list (deduped union of tag-tasks + direct tasks)."""

    tasks: list[TaskResponse]
