"""Pydantic schemas for the Notification resource."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    """Payload accepted when creating a new notification.

    Attributes:
        source: Identifier for the system or component creating the notification.
        content: Human-readable notification text (max 500 characters).
    """

    source: str = Field(min_length=1, max_length=100)
    content: str = Field(max_length=500)


class NotificationResponse(BaseModel):
    """Response schema returned for notification resources.

    Attributes:
        id: Auto-increment primary key.
        source: Identifier for the system or component that created the notification.
        content: Human-readable notification text.
        is_read: ``True`` once the notification has been acknowledged.
        created_at: UTC timestamp when the notification was created.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    content: str
    is_read: bool
    created_at: datetime
