"""Pydantic schemas for WorkLog request and response payloads."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

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
