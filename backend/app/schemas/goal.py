"""Pydantic schemas for Goal request and response payloads."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.task import TaskResponse


class GoalCreate(BaseModel):
    """Payload required to create a new Goal."""

    title: str
    description: str | None = None
    target_date: date | None = None
    tag_names: list[str] = []
    task_ids: list[int] = []


class GoalUpdate(BaseModel):
    """Payload for partial updates to a Goal.

    Pass ``target_date="CLEAR"`` to remove the target date.
    """

    title: str | None = None
    description: str | None = None
    target_date: str | None = None  # ISO date string, or "CLEAR" sentinel
    tag_names: list[str] | None = None
    task_ids: list[int] | None = None


class GoalStatusUpdate(BaseModel):
    """Payload for changing a Goal's status."""

    status: str  # 'active' | 'completed'


class GoalResponse(BaseModel):
    """Serialised representation of a Goal returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    target_date: date | None
    status: str
    completed_at: datetime | None
    created_at: datetime
    tags: list[str]
    total_tasks: int
    completed_tasks: int
    progress_pct: int  # 0-100

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags(cls, v: Any) -> list[str]:
        """Convert ORM Tag objects to plain name strings."""
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(item)
            else:
                result.append(item.name)
        return result


class GoalDetailResponse(GoalResponse):
    """Goal response with full task list (deduped union of tag-tasks + direct tasks)."""

    tasks: list[TaskResponse]
