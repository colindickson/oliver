"""Service layer for Goal domain logic."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import GoalNotFoundError
from app.models.goal import (
    Goal,
    goal_tags_table,
    goal_tasks_table,
)
from oliver_shared import STATUS_GOAL_ACTIVE, STATUS_GOAL_COMPLETED
from app.models.tag import Tag, task_tags_table
from app.models.task import Task
from app.schemas.goal import GoalCreate, GoalDetailResponse, GoalResponse, GoalUpdate
from app.services.tag_service import TagService
from oliver_shared import STATUS_COMPLETED, STATUS_ROLLED_FORWARD


class GoalService:
    """Encapsulates all Goal-related queries and write operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_all_goals(self) -> list[GoalResponse]:
        """Return unarchived goals with progress computed, ordered by created_at desc."""
        result = await self._db.execute(
            select(Goal).where(Goal.archived_at.is_(None))
        )
        goals = list(result.scalars().all())

        progress_map = await self._batch_compute_progress(goals)

        return [self._to_response(g, *progress_map[g.id]) for g in goals]

    async def get_goal(self, goal_id: int) -> GoalDetailResponse:
        """Return a goal with full task list and progress."""
        goal = await self._get_goal_or_raise(goal_id)
        total, completed, pct = await self._compute_progress(goal)
        tasks = await self._get_effective_tasks(goal)

        return self._to_response(goal, total, completed, pct, tasks=tasks)  # type: ignore[return-value]

    async def get_archived_goals(self) -> list[GoalResponse]:
        """Return all archived goals with progress, ordered by archived_at desc."""
        result = await self._db.execute(
            select(Goal)
            .where(Goal.archived_at.is_not(None))
            .order_by(Goal.archived_at.desc())
        )
        goals = list(result.scalars().all())

        progress_map = await self._batch_compute_progress(goals)

        return [self._to_response(g, *progress_map[g.id]) for g in goals]

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
        await self._db.flush()
        await self._db.refresh(goal)

        return self._to_response(goal, total, completed, pct)

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
                goal.target_date = date.fromisoformat(payload.target_date)
        if payload.tag_names is not None:
            goal.tags = await self._resolve_tags(payload.tag_names)
        if payload.task_ids is not None:
            goal.direct_tasks = await self._resolve_tasks(payload.task_ids)

        await self._db.flush()
        await self._maybe_auto_complete(goal)

        await self._db.flush()
        await self._db.refresh(goal)

        total, completed, pct = await self._compute_progress(goal)
        return self._to_response(goal, total, completed, pct)

    async def set_goal_status(self, goal_id: int, status: str) -> GoalResponse:
        """Manually set the status of a goal."""
        goal = await self._get_goal_or_raise(goal_id)
        goal.status = status
        if status == STATUS_GOAL_COMPLETED:
            goal.completed_at = datetime.now(timezone.utc)
        else:
            goal.completed_at = None

        await self._db.flush()
        await self._db.refresh(goal)

        total, completed, pct = await self._compute_progress(goal)
        return self._to_response(goal, total, completed, pct)

    async def archive_goal(self, goal_id: int) -> GoalResponse:
        """Archive a goal by setting archived_at."""
        goal = await self._get_goal_or_raise(goal_id)
        goal.archived_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.refresh(goal)
        total, completed, pct = await self._compute_progress(goal)
        return self._to_response(goal, total, completed, pct)

    async def unarchive_goal(self, goal_id: int) -> GoalResponse:
        """Unarchive a goal by clearing archived_at."""
        goal = await self._get_goal_or_raise(goal_id)
        goal.archived_at = None
        await self._db.flush()
        await self._db.refresh(goal)
        total, completed, pct = await self._compute_progress(goal)
        return self._to_response(goal, total, completed, pct)

    async def delete_goal(self, goal_id: int) -> None:
        """Delete a goal (cascade removes junction rows; tasks/tags are unaffected)."""
        goal = await self._get_goal_or_raise(goal_id)
        await self._db.delete(goal)
        await self._db.flush()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_response(
        self, goal: Goal, total: int, completed: int, pct: int, **extra: object
    ) -> GoalResponse:
        """Build a GoalResponse (or GoalDetailResponse via tasks kwarg)."""
        response_cls = GoalDetailResponse if "tasks" in extra else GoalResponse
        return response_cls(
            id=goal.id,
            title=goal.title,
            description=goal.description,
            target_date=goal.target_date,
            status=goal.status,
            completed_at=goal.completed_at,
            archived_at=goal.archived_at,
            created_at=goal.created_at,
            tags=goal.tags,
            total_tasks=total,
            completed_tasks=completed,
            progress_pct=pct,
            **extra,
        )

    async def _get_goal_or_raise(self, goal_id: int) -> Goal:
        result = await self._db.execute(select(Goal).where(Goal.id == goal_id))
        goal = result.scalar_one_or_none()
        if goal is None:
            raise GoalNotFoundError(goal_id)
        return goal

    async def _resolve_tags(self, tag_names: list[str]) -> list[Tag]:
        """Return Tag ORM objects for the given names, creating any that are missing."""
        tag_svc = TagService(self._db)
        return await tag_svc.resolve_tags(tag_names)

    async def _resolve_tasks(self, task_ids: list[int]) -> list[Task]:
        """Return Task ORM objects for the given IDs (silently skips missing IDs)."""
        if not task_ids:
            return []
        result = await self._db.execute(select(Task).where(Task.id.in_(task_ids)))
        return list(result.scalars().all())

    async def _batch_compute_progress(
        self, goals: list[Goal]
    ) -> dict[int, tuple[int, int, int]]:
        """Compute progress for all goals in a few queries instead of 2N.

        Returns:
            Dict mapping goal_id to (total_tasks, completed_tasks, progress_pct).
        """
        if not goals:
            return {}

        goal_ids = [g.id for g in goals]

        # Gather tag-linked task IDs per goal
        goal_tag_task_ids: dict[int, set[int]] = {gid: set() for gid in goal_ids}
        all_tag_ids: set[int] = set()
        for g in goals:
            for tag in g.tags:
                all_tag_ids.add(tag.id)

        if all_tag_ids:
            tag_rows = await self._db.execute(
                select(
                    task_tags_table.c.task_id,
                    task_tags_table.c.tag_id,
                ).where(task_tags_table.c.tag_id.in_(all_tag_ids))
            )
            task_tag_map: dict[int, set[int]] = {}
            for row in tag_rows:
                task_tag_map.setdefault(row.task_id, set()).add(row.tag_id)

            for goal in goals:
                required = {tag.id for tag in goal.tags}
                goal_tag_task_ids[goal.id] = {
                    tid for tid, ttags in task_tag_map.items()
                    if required.issubset(ttags)
                }

        # Gather direct task IDs per goal
        direct_rows = await self._db.execute(
            select(
                goal_tasks_table.c.goal_id,
                goal_tasks_table.c.task_id,
            ).where(goal_tasks_table.c.goal_id.in_(goal_ids))
        )
        goal_direct_task_ids: dict[int, set[int]] = {gid: set() for gid in goal_ids}
        for row in direct_rows:
            goal_direct_task_ids[row.goal_id].add(row.task_id)

        # Merge into effective task IDs
        all_task_ids: set[int] = set()
        goal_effective_ids: dict[int, set[int]] = {}
        for goal in goals:
            effective = goal_tag_task_ids[goal.id] | goal_direct_task_ids[goal.id]
            goal_effective_ids[goal.id] = effective
            all_task_ids.update(effective)

        if not all_task_ids:
            return {g.id: (0, 0, 0) for g in goals}

        # Single query for all task statuses
        task_rows = await self._db.execute(
            select(Task.id, Task.status).where(Task.id.in_(all_task_ids))
        )
        task_statuses: dict[int, str] = {row.id: row.status for row in task_rows}

        result: dict[int, tuple[int, int, int]] = {}
        for goal in goals:
            effective = goal_effective_ids[goal.id]
            statuses = [task_statuses[tid] for tid in effective if tid in task_statuses]
            statuses = [s for s in statuses if s != STATUS_ROLLED_FORWARD]
            total = len(statuses)
            if total == 0:
                result[goal.id] = (0, 0, 0)
            else:
                completed = sum(1 for s in statuses if s == STATUS_COMPLETED)
                pct = round(completed / total * 100)
                result[goal.id] = (total, completed, pct)
        return result

    async def _get_effective_tasks(self, goal: Goal) -> list[Task]:
        """Return the deduped union of tag-linked and directly-linked tasks."""
        tag_ids = [tag.id for tag in goal.tags]
        direct_task_ids = {t.id for t in goal.direct_tasks}

        tag_task_ids: set[int] = set()
        if tag_ids:
            stmt = (
                select(task_tags_table.c.task_id)
                .where(task_tags_table.c.tag_id.in_(tag_ids))
                .group_by(task_tags_table.c.task_id)
                .having(func.count(task_tags_table.c.tag_id) == len(tag_ids))
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
        tasks = [t for t in tasks if t.status != STATUS_ROLLED_FORWARD]
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
