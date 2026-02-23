"""Pydantic schemas for Tag request and response payloads."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.task import TaskResponse


class TagResponse(BaseModel):
    """Serialised representation of a Tag with usage count."""

    id: int
    name: str
    task_count: int


class TagTaskGroup(BaseModel):
    """Tasks grouped by day date for a tag detail view."""

    date: str
    tasks: list[TaskResponse]
