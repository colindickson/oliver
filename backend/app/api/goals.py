"""API routes for the Goal resource."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.goal import (
    GoalCreate,
    GoalDetailResponse,
    GoalResponse,
    GoalStatusUpdate,
    GoalUpdate,
)
from app.services.goal_service import GoalService

router = APIRouter(prefix="/api/goals", tags=["goals"])


@router.post("", response_model=GoalResponse, status_code=201)
async def create_goal(body: GoalCreate, db: AsyncSession = Depends(get_db)) -> GoalResponse:
    """Create a new goal."""
    return await GoalService(db).create_goal(body)


@router.get("", response_model=list[GoalResponse])
async def list_goals(db: AsyncSession = Depends(get_db)) -> list[GoalResponse]:
    """Return all goals with progress."""
    return await GoalService(db).get_all_goals()


@router.get("/{goal_id}", response_model=GoalDetailResponse)
async def get_goal(goal_id: int, db: AsyncSession = Depends(get_db)) -> GoalDetailResponse:
    """Return a single goal with full task list."""
    return await GoalService(db).get_goal(goal_id)


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: int, body: GoalUpdate, db: AsyncSession = Depends(get_db)
) -> GoalResponse:
    """Update mutable fields on a goal."""
    return await GoalService(db).update_goal(goal_id, body)


@router.patch("/{goal_id}/status", response_model=GoalResponse)
async def set_goal_status(
    goal_id: int, body: GoalStatusUpdate, db: AsyncSession = Depends(get_db)
) -> GoalResponse:
    """Manually set a goal's status (complete or reopen)."""
    return await GoalService(db).set_goal_status(goal_id, body.status)


@router.delete("/{goal_id}")
async def delete_goal(goal_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, bool]:
    """Delete a goal (tasks and tags are unaffected)."""
    await GoalService(db).delete_goal(goal_id)
    return {"deleted": True}
