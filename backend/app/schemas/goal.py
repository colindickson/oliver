"""Pydantic schemas for Goal request and response payloads."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas._shared import TagCoercionMixin
from app.schemas.task import TaskResponse


class GoalCreate(BaseModel):
    """Payload required to create a new Goal."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    target_date: date | None = None
    tag_names: list[str] = []
    task_ids: list[int] = []
    parent_goal_id: int | None = None


class GoalUpdate(BaseModel):
    """Payload for partial updates to a Goal.

    Set ``clear_target_date=True`` to remove the target date.
    Otherwise, pass a date value for ``target_date``.
    """

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    target_date: date | None = None
    clear_target_date: bool = False
    tag_names: list[str] | None = None
    task_ids: list[int] | None = None
    parent_goal_id: int | None = None
    clear_parent: bool = False


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
    status: Literal["active", "completed"]
    completed_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    tags: list[str]
    parent_goal_id: int | None
    sub_goal_count: int
    total_tasks: int
    completed_tasks: int
    progress_pct: int  # 0-100
    direct_total_tasks: int
    direct_completed_tasks: int
    direct_progress_pct: int  # 0-100, parent's own tasks only


class GoalDetailResponse(GoalResponse):
    """Goal response with full task list and direct sub-goals."""

    tasks: list[TaskResponse]
    sub_goals: list[GoalResponse] = []
