"""Service layer for Goal domain logic."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import GoalNotFoundError, InvalidOperationError
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

        progress = await self._batch_compute_progress(goals)
        counts = await self._child_count_map([g.id for g in goals])
        responses: list[GoalResponse] = []
        for g in goals:
            rolled, direct = progress[g.id]
            responses.append(
                self._to_response(
                    g, *rolled, direct=direct, sub_goal_count=counts.get(g.id, 0)
                )
            )
        return responses

    async def get_goal(self, goal_id: int) -> GoalDetailResponse:
        """Return a goal with full task list, sub-goals, and progress."""
        goal = await self._get_goal_or_raise(goal_id)
        tasks = await self._get_effective_tasks(goal)
        children = await self._get_children(goal)
        child_progress = await self._batch_compute_progress(children)
        sub_goals = []
        for c in children:
            rolled, direct = child_progress[c.id]
            sub_goals.append(self._to_response(c, *rolled, direct=direct))
        return await self._build_response(goal, tasks=tasks, sub_goals=sub_goals)  # type: ignore[return-value]

    async def get_archived_goals(self) -> list[GoalResponse]:
        """Return all archived goals with progress, ordered by archived_at desc."""
        result = await self._db.execute(
            select(Goal)
            .where(Goal.archived_at.is_not(None))
            .order_by(Goal.archived_at.desc())
        )
        goals = list(result.scalars().all())

        progress = await self._batch_compute_progress(goals)
        counts = await self._child_count_map([g.id for g in goals])
        responses: list[GoalResponse] = []
        for g in goals:
            rolled, direct = progress[g.id]
            responses.append(
                self._to_response(
                    g, *rolled, direct=direct, sub_goal_count=counts.get(g.id, 0)
                )
            )
        return responses

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def create_goal(self, payload: GoalCreate) -> GoalResponse:
        """Create a new goal, resolving tags and tasks."""
        tag_objects = await self._resolve_tags(payload.tag_names)
        task_objects = await self._resolve_tasks(payload.task_ids)

        if payload.parent_goal_id is not None:
            await self._validate_parent(None, payload.parent_goal_id)

        goal = Goal(
            title=payload.title,
            description=payload.description,
            target_date=payload.target_date,
            status=STATUS_GOAL_ACTIVE,
            parent_goal_id=payload.parent_goal_id,
            created_at=datetime.now(timezone.utc),
        )
        goal.tags = tag_objects
        goal.direct_tasks = task_objects
        self._db.add(goal)
        await self._db.flush()
        await self._db.refresh(goal)

        return await self._build_response(goal)

    async def update_goal(self, goal_id: int, payload: GoalUpdate) -> GoalResponse:
        """Apply partial updates to a goal."""
        goal = await self._get_goal_or_raise(goal_id)

        if payload.title is not None:
            goal.title = payload.title
        if payload.description is not None:
            goal.description = payload.description
        if payload.clear_target_date:
            goal.target_date = None
        elif payload.target_date is not None:
            goal.target_date = payload.target_date
        if payload.clear_parent:
            goal.parent_goal_id = None
        elif payload.parent_goal_id is not None:
            await self._validate_parent(goal.id, payload.parent_goal_id)
            goal.parent_goal_id = payload.parent_goal_id
        if payload.tag_names is not None:
            goal.tags = await self._resolve_tags(payload.tag_names)
        if payload.task_ids is not None:
            goal.direct_tasks = await self._resolve_tasks(payload.task_ids)

        await self._db.flush()
        await self._maybe_auto_complete(goal)

        await self._db.flush()
        await self._db.refresh(goal)

        return await self._build_response(goal)

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

        return await self._build_response(goal)

    async def archive_goal(self, goal_id: int) -> GoalResponse:
        """Archive a goal by setting archived_at."""
        goal = await self._get_goal_or_raise(goal_id)
        goal.archived_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.refresh(goal)
        return await self._build_response(goal)

    async def unarchive_goal(self, goal_id: int) -> GoalResponse:
        """Unarchive a goal by clearing archived_at."""
        goal = await self._get_goal_or_raise(goal_id)
        goal.archived_at = None
        await self._db.flush()
        await self._db.refresh(goal)
        return await self._build_response(goal)

    async def delete_goal(self, goal_id: int) -> None:
        """Delete a goal (cascade removes junction rows; tasks/tags are unaffected)."""
        goal = await self._get_goal_or_raise(goal_id)
        await self._db.delete(goal)
        await self._db.flush()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_response(
        self,
        goal: Goal,
        total: int,
        completed: int,
        pct: int,
        *,
        direct: tuple[int, int, int] | None = None,
        sub_goal_count: int = 0,
        **extra: object,
    ) -> GoalResponse:
        """Build a GoalResponse (or GoalDetailResponse when ``tasks`` is given)."""
        d_total, d_completed, d_pct = (
            direct if direct is not None else (total, completed, pct)
        )
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
            parent_goal_id=goal.parent_goal_id,
            sub_goal_count=sub_goal_count,
            total_tasks=total,
            completed_tasks=completed,
            progress_pct=pct,
            direct_total_tasks=d_total,
            direct_completed_tasks=d_completed,
            direct_progress_pct=d_pct,
            **extra,
        )

    async def _build_response(self, goal: Goal, **extra: object) -> GoalResponse:
        """Compute rolled-up subtree progress + own-only direct progress."""
        total, completed, pct = await self._compute_progress(goal)
        direct = await self._compute_direct_progress(goal)
        sub_goal_count = await self._count_children(goal)
        return self._to_response(
            goal, total, completed, pct, direct=direct,
            sub_goal_count=sub_goal_count, **extra,
        )

    async def _get_goal_or_raise(self, goal_id: int) -> Goal:
        result = await self._db.execute(select(Goal).where(Goal.id == goal_id))
        goal = result.scalar_one_or_none()
        if goal is None:
            raise GoalNotFoundError(goal_id)
        return goal

    async def _validate_parent(self, goal_id: int | None, parent_goal_id: int) -> None:
        """Enforce the one-level + no-cycle rules for assigning a parent.

        Args:
            goal_id: The goal being parented (None when creating a brand-new goal).
            parent_goal_id: The proposed parent.
        """
        if goal_id is not None and parent_goal_id == goal_id:
            raise InvalidOperationError("A goal cannot be its own parent.", 400)

        parent = await self._db.scalar(
            select(Goal).where(Goal.id == parent_goal_id)
        )
        if parent is None:
            raise InvalidOperationError(
                f"Parent goal {parent_goal_id} not found.", 400
            )
        if parent.parent_goal_id is not None:
            raise InvalidOperationError(
                "Sub-goals can only be nested one level deep.", 400
            )
        if goal_id is not None:
            child_count = await self._db.scalar(
                select(func.count())
                .select_from(Goal)
                .where(Goal.parent_goal_id == goal_id)
            )
            if child_count:
                raise InvalidOperationError(
                    "A goal with sub-goals cannot become a sub-goal.", 400
                )

    async def _get_children(self, goal: Goal) -> list[Goal]:
        result = await self._db.execute(
            select(Goal).where(Goal.parent_goal_id == goal.id)
        )
        return list(result.scalars().all())

    async def _count_children(self, goal: Goal) -> int:
        count = await self._db.scalar(
            select(func.count())
            .select_from(Goal)
            .where(Goal.parent_goal_id == goal.id)
        )
        return int(count or 0)

    async def _child_count_map(self, goal_ids: list[int]) -> dict[int, int]:
        if not goal_ids:
            return {}
        rows = await self._db.execute(
            select(Goal.parent_goal_id, func.count())
            .where(Goal.parent_goal_id.in_(goal_ids))
            .group_by(Goal.parent_goal_id)
        )
        return {pid: cnt for pid, cnt in rows if pid is not None}

    async def _resolve_tags(self, tag_names: list[str]) -> list[Tag]:
        """Return Tag ORM objects for the given names, creating any that are missing."""
        tag_svc = TagService(self._db)
        return await tag_svc.resolve_tags(tag_names)

    async def _resolve_tasks(self, task_ids: list[int]) -> list[Task]:
        """Return Task ORM objects for the given IDs, raising if any are missing."""
        if not task_ids:
            return []
        result = await self._db.execute(select(Task).where(Task.id.in_(task_ids)))
        tasks = list(result.scalars().all())
        if len(tasks) != len(task_ids):
            found_ids = {t.id for t in tasks}
            missing = [i for i in task_ids if i not in found_ids]
            raise InvalidOperationError(f"Task IDs not found: {missing}")
        return tasks

    async def _batch_own_ids(self, goals: list[Goal]) -> dict[int, set[int]]:
        """Own effective task IDs for each goal, in a few queries."""
        ids_map: dict[int, set[int]] = {g.id: set() for g in goals}
        goal_ids = [g.id for g in goals]

        if goal_ids:
            direct_rows = await self._db.execute(
                select(goal_tasks_table.c.goal_id, goal_tasks_table.c.task_id)
                .where(goal_tasks_table.c.goal_id.in_(goal_ids))
            )
            for gid, tid in direct_rows:
                ids_map[gid].add(tid)

        all_tag_ids = {tag.id for g in goals for tag in g.tags}
        if all_tag_ids:
            tag_rows = await self._db.execute(
                select(task_tags_table.c.task_id, task_tags_table.c.tag_id)
                .where(task_tags_table.c.tag_id.in_(all_tag_ids))
            )
            task_tag_map: dict[int, set[int]] = {}
            for tid, tag_id in tag_rows:
                task_tag_map.setdefault(tid, set()).add(tag_id)
            for g in goals:
                required = {tag.id for tag in g.tags}
                if not required:
                    continue
                for tid, ttags in task_tag_map.items():
                    if required.issubset(ttags):
                        ids_map[g.id].add(tid)
        return ids_map

    async def _batch_compute_progress(
        self, goals: list[Goal]
    ) -> dict[int, tuple[tuple[int, int, int], tuple[int, int, int]]]:
        """For each goal: (rolled_up, direct) progress triples.

        rolled_up = subtree (own + direct children); direct = own only.
        Computed in a bounded number of queries (no per-goal DB calls).
        """
        if not goals:
            return {}
        own = await self._batch_own_ids(goals)

        children_by_parent: dict[int, list[int]] = {}
        for g in goals:
            if g.parent_goal_id is not None:
                children_by_parent.setdefault(g.parent_goal_id, []).append(g.id)

        present = {g.id for g in goals}
        extra_children_result = await self._db.execute(
            select(Goal).where(Goal.parent_goal_id.in_([g.id for g in goals]))
        )
        extra_children = [
            c for c in extra_children_result.scalars().all() if c.id not in present
        ]
        if extra_children:
            extra_own = await self._batch_own_ids(extra_children)
            own.update(extra_own)
            for c in extra_children:
                children_by_parent.setdefault(c.parent_goal_id, []).append(c.id)

        rolled_ids: dict[int, set[int]] = {}
        for g in goals:
            ids = set(own.get(g.id, set()))
            for cid in children_by_parent.get(g.id, []):
                ids |= own.get(cid, set())
            rolled_ids[g.id] = ids

        all_ids: set[int] = set()
        for s in rolled_ids.values():
            all_ids |= s
        statuses: dict[int, str] = {}
        if all_ids:
            rows = await self._db.execute(
                select(Task.id, Task.status).where(Task.id.in_(all_ids))
            )
            statuses = {tid: st for tid, st in rows}

        def _tally(ids: set[int]) -> tuple[int, int, int]:
            st = [
                statuses[t] for t in ids
                if t in statuses and statuses[t] != STATUS_ROLLED_FORWARD
            ]
            total = len(st)
            if total == 0:
                return 0, 0, 0
            completed = sum(1 for s in st if s == STATUS_COMPLETED)
            return total, completed, round(completed / total * 100)

        return {
            g.id: (_tally(rolled_ids[g.id]), _tally(own.get(g.id, set())))
            for g in goals
        }

    async def _get_own_effective_task_ids(self, goal: Goal) -> set[int]:
        """Task IDs linked to THIS goal only (tag-AND union direct), no children."""
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

        return tag_task_ids | direct_task_ids

    async def _get_effective_tasks(self, goal: Goal) -> list[Task]:
        """Return the deduped union of tag-linked and directly-linked tasks."""
        all_ids = await self._get_own_effective_task_ids(goal)
        if not all_ids:
            return []
        result = await self._db.execute(select(Task).where(Task.id.in_(all_ids)))
        return list(result.scalars().all())

    async def _get_subtree_task_ids(self, goal: Goal) -> set[int]:
        """Own effective task IDs unioned with every child's own effective task IDs."""
        ids = await self._get_own_effective_task_ids(goal)
        for child in await self._get_children(goal):
            ids |= await self._get_own_effective_task_ids(child)
        return ids

    async def _progress_for_ids(self, task_ids: set[int]) -> tuple[int, int, int]:
        """(total, completed, pct) for a set of task IDs, excluding rolled_forward."""
        if not task_ids:
            return 0, 0, 0
        rows = await self._db.execute(
            select(Task.status).where(Task.id.in_(task_ids))
        )
        statuses = [s for (s,) in rows if s != STATUS_ROLLED_FORWARD]
        total = len(statuses)
        if total == 0:
            return 0, 0, 0
        completed = sum(1 for s in statuses if s == STATUS_COMPLETED)
        return total, completed, round(completed / total * 100)

    async def _compute_progress(self, goal: Goal) -> tuple[int, int, int]:
        """Rolled-up subtree progress (parent + its sub-goals)."""
        return await self._progress_for_ids(await self._get_subtree_task_ids(goal))

    async def _compute_direct_progress(self, goal: Goal) -> tuple[int, int, int]:
        """Progress over the goal's OWN effective tasks only."""
        own_ids = await self._get_own_effective_task_ids(goal)
        return await self._progress_for_ids(own_ids)

    async def _maybe_auto_complete(self, goal: Goal) -> None:
        """Auto-complete the goal if all tasks are done and goal is still active."""
        if goal.status != STATUS_GOAL_ACTIVE:
            return
        total, completed, _ = await self._compute_progress(goal)
        if total > 0 and completed == total:
            goal.status = STATUS_GOAL_COMPLETED
            goal.completed_at = datetime.now(timezone.utc)
