"""FastAPI route handlers for the /api/notifications resource.

IMPORTANT: The /unread route is declared before /{id}/read so that
FastAPI does not treat the literal string "unread" as an integer path
parameter and raise a 422 validation error.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.post("", response_model=NotificationResponse, status_code=201)
async def create_notification(
    body: NotificationCreate,
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    """Create a new notification.

    Args:
        body: Validated request body containing source and content.
        db: Injected async database session.

    Returns:
        The newly created notification.
    """
    service = NotificationService(db)
    notification = await service.create(body.source, body.content)
    await db.commit()
    return notification


# NOTE: /unread must appear before /{id}/read to avoid path-parameter collision.
@router.get("/unread", response_model=list[NotificationResponse])
async def list_unread_notifications(
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    """Return all unread notifications ordered by created_at descending.

    Args:
        db: Injected async database session.

    Returns:
        A list of unread notifications.
    """
    return await NotificationService(db).list_unread()


@router.get("", response_model=list[NotificationResponse])
async def list_recent_notifications(
    limit: int = Query(default=5, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    """Return the most recent notifications (default limit 5).

    Args:
        limit: Maximum number of notifications to return.
        db: Injected async database session.

    Returns:
        A list of recent notifications ordered by created_at descending.
    """
    return await NotificationService(db).list_recent(limit=limit)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    """Mark a notification as read.

    Args:
        notification_id: Primary key of the notification to update.
        db: Injected async database session.

    Returns:
        The updated notification with is_read set to True.

    Raises:
        HTTPException: 404 if the notification does not exist.
    """
    notification = await NotificationService(db).mark_read(notification_id)
    await db.commit()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification
