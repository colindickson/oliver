"""API routes for the Timer resource.

Exposes start, pause, stop, current-state, and session-history endpoints.
All state is persisted via TimerService into the settings table — no
background processes are required.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.timer import TimerAddTime, TimerSessionResponse, TimerStart, TimerState
from app.services.timer_service import TimerService

router = APIRouter(prefix="/api/timer", tags=["timer"])


@router.post("/start", response_model=TimerState)
async def start_timer(
    body: TimerStart, db: AsyncSession = Depends(get_db)
) -> TimerState:
    """Start or resume the timer for a task.

    If a paused timer for the same task exists it is resumed.  Returns 409
    if a different timer is already running.

    Args:
        body: Contains ``task_id`` identifying the task to time.
        db: Injected async database session.

    Returns:
        Current ``TimerState`` with ``status == "running"``.

    Raises:
        HTTPException: 409 if a timer is already running.
    """
    try:
        state = await TimerService(db).start(body.task_id)
        return TimerState(**state)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/pause", response_model=TimerState)
async def pause_timer(db: AsyncSession = Depends(get_db)) -> TimerState:
    """Pause the currently running timer.

    Args:
        db: Injected async database session.

    Returns:
        Current ``TimerState`` with ``status == "paused"``.

    Raises:
        HTTPException: 409 if no timer is running.
    """
    try:
        state = await TimerService(db).pause()
        return TimerState(**state)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/stop", response_model=TimerSessionResponse)
async def stop_timer(db: AsyncSession = Depends(get_db)) -> TimerSessionResponse:
    """Stop the active timer and persist a completed TimerSession.

    Args:
        db: Injected async database session.

    Returns:
        The newly created ``TimerSessionResponse`` with final duration.

    Raises:
        HTTPException: 409 if no timer is active.
    """
    try:
        session = await TimerService(db).stop()
        return session
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/current", response_model=TimerState)
async def get_current_timer(db: AsyncSession = Depends(get_db)) -> TimerState:
    """Return the current timer state with live elapsed seconds.

    Args:
        db: Injected async database session.

    Returns:
        ``TimerState`` — ``status`` is ``idle`` when no timer is active.
    """
    state = await TimerService(db).get_current()
    return TimerState(**state)


@router.get("/sessions/{task_id}", response_model=list[TimerSessionResponse])
async def get_timer_sessions(
    task_id: int, db: AsyncSession = Depends(get_db)
) -> list[TimerSessionResponse]:
    """Return all completed timer sessions for a task, newest first.

    Args:
        task_id: Primary key of the task whose sessions to retrieve.
        db: Injected async database session.

    Returns:
        Ordered list of ``TimerSessionResponse`` objects.
    """
    return await TimerService(db).get_sessions_for_task(task_id)


@router.post("/add-time", response_model=TimerSessionResponse)
async def add_time(
    body: TimerAddTime, db: AsyncSession = Depends(get_db)
) -> TimerSessionResponse:
    """Manually credit time to a task by creating a TimerSession record.

    Does not interact with any active timer state machine.

    Args:
        body: Contains ``task_id`` and ``seconds`` to credit.
        db: Injected async database session.

    Returns:
        The newly created ``TimerSessionResponse``.
    """
    session = await TimerService(db).add_time(body.task_id, body.seconds)
    return session
