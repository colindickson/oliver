"""Pydantic schemas for Task request and response payloads."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    """Payload required to create a new Task.

    Attributes:
        day_id: Foreign key linking the task to its parent Day.
        category: One of ``deep_work``, ``short_task``, or ``maintenance``.
        title: Short human-readable label.
        description: Optional extended notes.
        order_index: Display position within the category; defaults to 0.
    """

    day_id: int
    category: str
    title: str
    description: str | None = None
    order_index: int = 0


class TaskUpdate(BaseModel):
    """Payload for partial or full updates to a Task.

    All fields are optional so callers may send only the fields they want
    changed.

    Attributes:
        title: Replacement title string.
        description: Replacement description string.
        order_index: New display position.
    """

    title: str | None = None
    description: str | None = None
    order_index: int | None = None


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
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    day_id: int
    category: str
    title: str
    description: str | None
    status: str
    order_index: int
    completed_at: datetime | None
