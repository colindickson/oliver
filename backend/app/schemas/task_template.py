"""Pydantic schemas for the TaskTemplate resource."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class TemplateCreate(BaseModel):
    title: str
    description: str | None = None
    category: str | None = None
    tags: list[str] = []


class TemplateUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    category: str | None
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime

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


class InstantiatePayload(BaseModel):
    day_id: int
    category: str | None = None
