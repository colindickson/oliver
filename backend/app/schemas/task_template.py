"""Pydantic schemas for the TaskTemplate resource."""

from __future__ import annotations

from datetime import date as date_type, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas._shared import TagCoercionMixin

RecurrenceType = Literal["weekly", "bi_weekly", "monthly"]


class TemplateCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category: Literal["deep_work", "short_task", "maintenance"] | None = None
    tags: list[str] = []


class TemplateUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None


class TemplateResponse(TagCoercionMixin):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    category: str | None
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime


class InstantiatePayload(BaseModel):
    day_id: int
    category: str | None = None


class ScheduleCreate(BaseModel):
    recurrence: RecurrenceType
    anchor_date: date_type


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    recurrence: RecurrenceType
    anchor_date: date_type
    next_run_date: date_type
    created_at: datetime
