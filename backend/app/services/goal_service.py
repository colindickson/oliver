"""Service layer for Goal domain logic."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal, STATUS_GOAL_ACTIVE, STATUS_GOAL_COMPLETED, goal_tags_table, goal_tasks_table
from app.models.tag import Tag, task_tags_table
from app.models.task import Task
from app.schemas.goal import GoalCreate, GoalDetailResponse, GoalResponse, GoalUpdate
from app.services.tag_service import TagService
from oliver_shared import STATUS_COMPLETED


class GoalService:
    """Encapsulates all Goal-related queries and write operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_all_goals(self) -> list[GoalResponse]:
        """Return all goals with progress computed, ordered by created_at desc."""
        result = await self._db.execute(select(Goal))
        goals = list(result.scalars().all())

        responses = []
        for goal in goals:
            total, completed, pct = await self._compute_progress(goal)
            responses.append(
                GoalResponse(
                    id=goal.id,
                    title=goal.title,
                    description=goal.description,
                    target_date=goal.target_date,
                    status=goal.status,
                    completed_at=goal.completed_at,
                    created_at=goal.created_at,
                    tags=goal.tags,  # field_validator coerces Tag objects to strings
                    total_tasks=total,
                    completed_tasks=completed,
                    progress_pct=pct,
                )
            )
        return responses

    async def get_goal(self, goal_id: int) -> GoalDetailResponse:
        """Return a goal with full task list and progress."""
        goal = await self._get_goal_or_raise(goal_id)
        total, completed, pct = await self._compute_progress(goal)
        tasks = await self._get_effective_tasks(goal)

        return GoalDetailResponse(
            id=goal.id,
            title=goal.title,
            description=goal.description,
            target_date=goal.target_date,
            status=goal.status,
            completed_at=goal.completed_at,
            created_at=goal.created_at,
            tags=goal.tags,
            total_tasks=total,
            completed_tasks=completed,
            progress_pct=pct,
            tasks=tasks,
        )

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def create_goal(self, payload: GoalCreate) -> GoalResponse:
        """Create a new goal, resolving tags and tasks."""
        tag_objects = await self._resolve_tags(payload.tag_names)
        task_objects = await self._resolve_tasks(payload.task_ids)

        goal = Goal(
            title=payload.title,
            description=payload.description,
            target_date=payload.target_date,
            status=STATUS_GOAL_ACTIVE,
            created_at=datetime.now(timezone.utc),
        )
        goal.tags = tag_objects
        goal.direct_tasks = task_objects
        self._db.add(goal)
        await self._db.flush()
        await self._db.refresh(goal)

        total, completed, pct = await self._compute_progress(goal)
        await self._db.commit()
        await self._db.refresh(goal)

        return GoalResponse(
            id=goal.id,
            title=goal.title,
            description=goal.description,
            target_date=goal.target_date,
            status=goal.status,
            completed_at=goal.completed_at,
            created_at=goal.created_at,
            tags=goal.tags,
            total_tasks=total,
            completed_tasks=completed,
            progress_pct=pct,
        )

    async def update_goal(self, goal_id: int, payload: GoalUpdate) -> GoalResponse:
        """Apply partial updates to a goal."""
        goal = await self._get_goal_or_raise(goal_id)

        if payload.title is not None:
            goal.title = payload.title
        if payload.description is not None:
            goal.description = payload.description
        if payload.target_date is not None:
            if payload.target_date == "CLEAR":
                goal.target_date = None
            else:
                from datetime import date
                goal.target_date = date.fromisoformat(payload.target_date)
        if payload.tag_names is not None:
            goal.tags = await self._resolve_tags(payload.tag_names)
        if payload.task_ids is not None:
            goal.direct_tasks = await self._resolve_tasks(payload.task_ids)

        await self._db.flush()
        await self._maybe_auto_complete(goal)

        await self._db.commit()
        await self._db.refresh(goal)

        total, completed, pct = await self._compute_progress(goal)
        return GoalResponse(
            id=goal.id,
            title=goal.title,
            description=goal.description,
            target_date=goal.target_date,
            status=goal.status,
            completed_at=goal.completed_at,
            created_at=goal.created_at,
            tags=goal.tags,
            total_tasks=total,
            completed_tasks=completed,
            progress_pct=pct,
        )

    async def set_goal_status(self, goal_id: int, status: str) -> GoalResponse:
        """Manually set the status of a goal."""
        goal = await self._get_goal_or_raise(goal_id)
        goal.status = status
        if status == STATUS_GOAL_COMPLETED:
            goal.completed_at = datetime.now(timezone.utc)
        else:
            goal.completed_at = None

        await self._db.commit()
        await self._db.refresh(goal)

        total, completed, pct = await self._compute_progress(goal)
        return GoalResponse(
            id=goal.id,
            title=goal.title,
            description=goal.description,
            target_date=goal.target_date,
            status=goal.status,
            completed_at=goal.completed_at,
            created_at=goal.created_at,
            tags=goal.tags,
            total_tasks=total,
            completed_tasks=completed,
            progress_pct=pct,
        )

    async def delete_goal(self, goal_id: int) -> None:
        """Delete a goal (cascade removes junction rows; tasks/tags are unaffected)."""
        goal = await self._get_goal_or_raise(goal_id)
        await self._db.delete(goal)
        await self._db.commit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_goal_or_raise(self, goal_id: int) -> Goal:
        from fastapi import HTTPException

        result = await self._db.execute(select(Goal).where(Goal.id == goal_id))
        goal = result.scalar_one_or_none()
        if goal is None:
            raise HTTPException(status_code=404, detail="Goal not found")
        return goal

    async def _resolve_tags(self, tag_names: list[str]) -> list[Tag]:
        """Return Tag ORM objects for the given names, creating any that are missing."""
        if not tag_names:
            return []
        tag_svc = TagService(self._db)
        return [await tag_svc.get_or_create_tag(name) for name in tag_names]

    async def _resolve_tasks(self, task_ids: list[int]) -> list[Task]:
        """Return Task ORM objects for the given IDs (silently skips missing IDs)."""
        if not task_ids:
            return []
        result = await self._db.execute(select(Task).where(Task.id.in_(task_ids)))
        return list(result.scalars().all())

    async def _get_effective_tasks(self, goal: Goal) -> list[Task]:
        """Return the deduped union of tag-linked and directly-linked tasks."""
        tag_ids = [tag.id for tag in goal.tags]
        direct_task_ids = {t.id for t in goal.direct_tasks}

        tag_task_ids: set[int] = set()
        if tag_ids:
            stmt = (
                select(task_tags_table.c.task_id)
                .where(task_tags_table.c.tag_id.in_(tag_ids))
            )
            rows = await self._db.execute(stmt)
            tag_task_ids = {row[0] for row in rows}

        all_ids = tag_task_ids | direct_task_ids
        if not all_ids:
            return []

        result = await self._db.execute(select(Task).where(Task.id.in_(all_ids)))
        return list(result.scalars().all())

    async def _compute_progress(self, goal: Goal) -> tuple[int, int, int]:
        """Return (total_tasks, completed_tasks, progress_pct) for the goal."""
        tasks = await self._get_effective_tasks(goal)
        total = len(tasks)
        if total == 0:
            return 0, 0, 0
        completed = sum(1 for t in tasks if t.status == STATUS_COMPLETED)
        pct = round(completed / total * 100)
        return total, completed, pct

    async def _maybe_auto_complete(self, goal: Goal) -> None:
        """Auto-complete the goal if all tasks are done and goal is still active."""
        if goal.status != STATUS_GOAL_ACTIVE:
            return
        total, completed, _ = await self._compute_progress(goal)
        if total > 0 and completed == total:
            goal.status = STATUS_GOAL_COMPLETED
            goal.completed_at = datetime.now(timezone.utc)
