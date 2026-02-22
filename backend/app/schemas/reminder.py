"""Pydantic schemas for the Reminder resource."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReminderCreate(BaseModel):
    """Payload accepted when creating a new reminder.

    Attributes:
        task_id: The task this reminder is associated with.
        remind_at: UTC datetime at which the reminder should fire.
        message: Human-readable notification text.
    """

    task_id: int
    remind_at: datetime
    message: str


class ReminderResponse(BaseModel):
    """Response schema returned for reminder resources.

    Attributes:
        id: Auto-increment primary key.
        task_id: The task this reminder belongs to.
        remind_at: UTC datetime at which the reminder should fire.
        message: Human-readable notification text.
        is_delivered: ``True`` once the notification has been dispatched.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    remind_at: datetime
    message: str
    is_delivered: bool
