"""Pydantic schemas for Task request and response payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class TaskCreate(BaseModel):
    """Payload required to create a new Task.

    Attributes:
        day_id: Foreign key linking the task to its parent Day.
        category: One of ``deep_work``, ``short_task``, or ``maintenance``.
        title: Short human-readable label.
        description: Optional extended notes.
        order_index: Display position within the category; defaults to 0.
        tags: Tag names to apply (max 5, stored lowercase without #).
    """

    day_id: int
    category: str
    title: str
    description: str | None = None
    order_index: int = 0
    tags: list[str] = []


class TaskUpdate(BaseModel):
    """Payload for partial or full updates to a Task.

    All fields are optional so callers may send only the fields they want
    changed.

    Attributes:
        title: Replacement title string.
        description: Replacement description string.
        order_index: New display position.
        tags: Replacement tag list. None = don't touch; [] = remove all.
    """

    title: str | None = None
    description: str | None = None
    order_index: int | None = None
    tags: list[str] | None = None


class TaskStatusUpdate(BaseModel):
    """Payload for changing a Task's lifecycle status.

    Attributes:
        status: One of ``pending``, ``in_progress``, or ``completed``.
    """

    status: str


class TaskReorder(BaseModel):
    """Payload for bulk reordering of Tasks.

    Attributes:
        task_ids: Ordered list of task primary keys.  The list position
            becomes the new ``order_index`` value for each task.
    """

    task_ids: list[int]


class BacklogTaskCreate(BaseModel):
    """Payload to create a backlog task (no day_id required).

    Attributes:
        title: Short human-readable label.
        description: Optional extended notes.
        category: Optional category — can be set now or when moving to a day.
        tags: Tag names to apply (max 5, stored lowercase without #).
    """

    title: str
    description: str | None = None
    category: str | None = None
    tags: list[str] = []


class MoveToDayPayload(BaseModel):
    """Payload to move a backlog task to a specific day.

    Attributes:
        day_id: The day to move the task to.
        category: Optional category override. If not provided, uses existing category.
    """

    day_id: int
    category: str | None = None


class TaskResponse(BaseModel):
    """Serialised representation of a Task returned by the API.

    Attributes:
        id: Primary key.
        day_id: Parent Day foreign key.
        category: Task category string.
        title: Short label.
        description: Optional extended notes.
        status: Current lifecycle status.
        order_index: Display position within the category.
        completed_at: UTC timestamp set when status becomes ``completed``.
        tags: List of tag name strings applied to this task.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    day_id: int | None
    category: str | None
    title: str
    description: str | None
    status: str
    order_index: int
    completed_at: datetime | None
    tags: list[str] = []

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
