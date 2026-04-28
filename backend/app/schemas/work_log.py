"""Pydantic schemas for WorkLog request and response payloads."""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas._shared import TagCoercionMixin


class WorkLogResponse(TagCoercionMixin):
    """Serialised representation of a WorkLog returned by the API.

    Attributes:
        id: Primary key.
        day_id: Parent Day foreign key.
        project_name: Name of the project this work log is associated with.
        description: Extended description of work done.
        created_at: UTC timestamp set at row creation.
        tags: List of tag name strings applied to this work log.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    day_id: int
    project_name: str
    description: str
    log_type: str | None = None
    created_at: datetime
    tags: list[str] = []


class WorkLogTagsUpdate(BaseModel):
    """Payload for updating tags on a WorkLog.

    Attributes:
        tags: Replacement tag list. [] removes all tags.
    """

    tags: list[str] = []


class WorkLogUpdate(BaseModel):
    """Payload for updating project_name or description on a WorkLog."""

    project_name: str | None = None
    description: str | None = None
    log_type: Literal["commit", "pr", "review", "research"] | None = None


class WorkLogCreate(BaseModel):
    """Payload for a single work log entry in a batch request."""

    project_name: str
    description: str
    date: date_type
    tags: list[str] = []
    log_type: Literal["commit", "pr", "review", "research"] | None = None


class WorkLogBatchCreate(BaseModel):
    """Payload for creating multiple work log entries atomically."""

    entries: list[WorkLogCreate] = Field(min_length=1)
