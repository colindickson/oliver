"""FastAPI route handlers for the /api/reminders resource.

IMPORTANT: The /due route is declared before /{reminder_id} routes so
that FastAPI does not treat the literal string "due" as an integer path
parameter and raise a 422 validation error.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.reminder import ReminderCreate, ReminderResponse
from app.services.reminder_service import ReminderService

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.post("", response_model=ReminderResponse, status_code=201)
async def create_reminder(
    body: ReminderCreate,
    db: AsyncSession = Depends(get_db),
) -> ReminderResponse:
    """Create a new reminder for a task.

    Args:
        body: Validated request body containing task_id, remind_at, and message.
        db: Injected async database session.

    Returns:
        The newly created reminder.
    """
    service = ReminderService(db)
    return await service.create(body.task_id, body.remind_at, body.message)


@router.get("", response_model=list[ReminderResponse])
async def list_reminders(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[ReminderResponse]:
    """List all reminders for the given task.

    Args:
        task_id: Query parameter — filters reminders to this task.
        db: Injected async database session.

    Returns:
        A list of reminders ordered by remind_at ascending.
    """
    return await ReminderService(db).list_for_task(task_id)


# NOTE: /due must appear before /{reminder_id} to avoid path-parameter collision.
@router.get("/due", response_model=list[ReminderResponse])
async def get_due_reminders(
    db: AsyncSession = Depends(get_db),
) -> list[ReminderResponse]:
    """Return all undelivered reminders whose remind_at is in the past.

    Args:
        db: Injected async database session.

    Returns:
        A list of due, undelivered reminders ordered by remind_at ascending.
    """
    return await ReminderService(db).get_due()


@router.patch("/{reminder_id}/delivered", response_model=ReminderResponse)
async def mark_delivered(
    reminder_id: int,
    db: AsyncSession = Depends(get_db),
) -> ReminderResponse:
    """Mark a reminder as delivered.

    Args:
        reminder_id: Primary key of the reminder to update.
        db: Injected async database session.

    Returns:
        The updated reminder with is_delivered set to True.

    Raises:
        HTTPException: 404 if the reminder does not exist.
    """
    reminder = await ReminderService(db).mark_delivered(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Delete a reminder by primary key.

    Args:
        reminder_id: Primary key of the reminder to delete.
        db: Injected async database session.

    Returns:
        ``{"deleted": True}`` on success.

    Raises:
        HTTPException: 404 if the reminder does not exist.
    """
    deleted = await ReminderService(db).delete(reminder_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"deleted": True}
