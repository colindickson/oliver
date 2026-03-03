"""Service layer for MCP log listing and reverting operations."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Callable, Awaitable

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_note import DailyNote
from app.models.day import Day
from app.models.day_metadata import DayMetadata
from app.models.day_off import DayOff
from app.models.mcp_log import MCPLog
from app.models.notification import Notification
from app.models.roadblock import Roadblock
from app.models.setting import Setting
from app.models.tag import Tag
from app.models.task import Task
from app.models.timer_session import TimerSession

_RECURRING_DAYS_OFF_KEY = "recurring_days_off"
_ACTIVE_TIMER_KEY = "active_timer"

# Type alias for revert handler
_Handler = Callable[[AsyncSession, MCPLog], Awaitable[None]]


async def _revert_create_task(db: AsyncSession, log: MCPLog) -> None:
    result_data = json.loads(log.result) if log.result else {}
    task_id = result_data.get("id")
    if task_id:
        await db.execute(delete(Task).where(Task.id == task_id))


async def _revert_update_task(db: AsyncSession, log: MCPLog) -> None:
    params = json.loads(log.params)
    before = json.loads(log.before_state) if log.before_state else {}
    task_id = params.get("task_id")
    if not task_id:
        return
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return
    task.title = before.get("title", task.title)
    task.description = before.get("description", task.description)
    task.status = before.get("status", task.status)
    task.category = before.get("category", task.category)

    # Restore tags
    tag_names: list[str] = before.get("tags", [])
    tags = []
    for name in tag_names:
        tag_result = await db.execute(select(Tag).where(Tag.name == name))
        tag = tag_result.scalar_one_or_none()
        if tag:
            tags.append(tag)
    task.tags = tags


async def _revert_delete_task(db: AsyncSession, log: MCPLog) -> None:
    before = json.loads(log.before_state) if log.before_state else {}
    day_date_str = before.get("day_date")
    if not day_date_str:
        return
    target_date = date.fromisoformat(day_date_str)
    result = await db.execute(select(Day).where(Day.date == target_date))
    day = result.scalar_one_or_none()
    if day is None:
        day = Day(
            date=target_date,
            created_at=datetime.now(timezone.utc),
        )
        db.add(day)
        await db.flush()

    task = Task(
        day_id=day.id,
        title=before.get("title", ""),
        description=before.get("description"),
        status=before.get("status", "pending"),
        category=before.get("category"),
        order_index=0,
    )
    db.add(task)
    await db.flush()

    tag_names: list[str] = before.get("tags", [])
    tags = []
    for name in tag_names:
        tag_result = await db.execute(select(Tag).where(Tag.name == name))
        tag = tag_result.scalar_one_or_none()
        if tag:
            tags.append(tag)
    task.tags = tags


async def _revert_complete_task(db: AsyncSession, log: MCPLog) -> None:
    params = json.loads(log.params)
    before = json.loads(log.before_state) if log.before_state else {}
    task_id = params.get("task_id")
    if not task_id:
        return
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return
    task.status = before.get("status", task.status)
    completed_at_str = before.get("completed_at")
    task.completed_at = (
        datetime.fromisoformat(completed_at_str) if completed_at_str else None
    )


async def _revert_set_daily_plan(db: AsyncSession, log: MCPLog) -> None:
    before = json.loads(log.before_state) if log.before_state else {}
    params = json.loads(log.params)
    date_str = params.get("date_str", "")
    target_date = date.fromisoformat(date_str) if date_str else date.today()

    result = await db.execute(select(Day).where(Day.date == target_date))
    day = result.scalar_one_or_none()
    if not day:
        return

    note_content = before.get("note")
    note_result = await db.execute(select(DailyNote).where(DailyNote.day_id == day.id))
    note = note_result.scalar_one_or_none()
    if note_content is not None:
        if note:
            note.content = note_content
        else:
            db.add(DailyNote(day_id=day.id, content=note_content))
    elif note:
        await db.delete(note)


async def _revert_mark_day_off(db: AsyncSession, log: MCPLog) -> None:
    params = json.loads(log.params)
    date_str = params.get("date_str", "")
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return
    result = await db.execute(select(Day).where(Day.date == target_date))
    day = result.scalar_one_or_none()
    if day:
        await db.execute(delete(DayOff).where(DayOff.day_id == day.id))


async def _revert_unmark_day_off(db: AsyncSession, log: MCPLog) -> None:
    before = json.loads(log.before_state) if log.before_state else {}
    if not before:
        return
    day_date_str = before.get("day_date", "")
    try:
        target_date = date.fromisoformat(day_date_str)
    except ValueError:
        return
    result = await db.execute(select(Day).where(Day.date == target_date))
    day = result.scalar_one_or_none()
    if not day:
        day = Day(date=target_date, created_at=datetime.now(timezone.utc))
        db.add(day)
        await db.flush()
    # Remove any existing day_off first (idempotent)
    await db.execute(delete(DayOff).where(DayOff.day_id == day.id))
    db.add(DayOff(
        day_id=day.id,
        reason=before.get("reason", "personal_day"),
        note=before.get("note"),
    ))


async def _revert_set_recurring_days_off(db: AsyncSession, log: MCPLog) -> None:
    before = json.loads(log.before_state) if log.before_state else {}
    days = before.get("days", [])
    result = await db.execute(
        select(Setting).where(Setting.key == _RECURRING_DAYS_OFF_KEY)
    )
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = json.dumps(days)
    else:
        db.add(Setting(key=_RECURRING_DAYS_OFF_KEY, value=json.dumps(days)))


async def _revert_set_day_metadata(db: AsyncSession, log: MCPLog) -> None:
    before = json.loads(log.before_state) if log.before_state else None
    params = json.loads(log.params)
    date_str = params.get("date_str", "")
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return
    result = await db.execute(select(Day).where(Day.date == target_date))
    day = result.scalar_one_or_none()
    if not day:
        return
    meta_result = await db.execute(
        select(DayMetadata).where(DayMetadata.day_id == day.id)
    )
    meta = meta_result.scalar_one_or_none()
    if before is None:
        if meta:
            await db.delete(meta)
    else:
        if meta:
            meta.temperature_c = before.get("temperature_c")
            meta.condition = before.get("condition")
            meta.moon_phase = before.get("moon_phase")
        else:
            db.add(DayMetadata(
                day_id=day.id,
                temperature_c=before.get("temperature_c"),
                condition=before.get("condition"),
                moon_phase=before.get("moon_phase"),
            ))


async def _revert_notify(db: AsyncSession, log: MCPLog) -> None:
    result_data = json.loads(log.result) if log.result else {}
    notif_id = result_data.get("id")
    if notif_id:
        await db.execute(delete(Notification).where(Notification.id == notif_id))


async def _revert_start_timer(db: AsyncSession, log: MCPLog) -> None:
    before = json.loads(log.before_state) if log.before_state else {}
    prior_state = before.get("active_timer")
    result = await db.execute(
        select(Setting).where(Setting.key == _ACTIVE_TIMER_KEY)
    )
    setting = result.scalar_one_or_none()
    if prior_state is None:
        if setting:
            await db.delete(setting)
    else:
        if setting:
            setting.value = json.dumps(prior_state)
        else:
            db.add(Setting(key=_ACTIVE_TIMER_KEY, value=json.dumps(prior_state)))


async def _revert_stop_timer(db: AsyncSession, log: MCPLog) -> None:
    result_data = json.loads(log.result) if log.result else {}
    before = json.loads(log.before_state) if log.before_state else {}
    timer_session_id = result_data.get("timer_session_id")
    if timer_session_id:
        await db.execute(
            delete(TimerSession).where(TimerSession.id == timer_session_id)
        )
    prior_state = before.get("active_timer")
    result = await db.execute(
        select(Setting).where(Setting.key == _ACTIVE_TIMER_KEY)
    )
    setting = result.scalar_one_or_none()
    if prior_state is not None:
        if setting:
            setting.value = json.dumps(prior_state)
        else:
            db.add(Setting(key=_ACTIVE_TIMER_KEY, value=json.dumps(prior_state)))


REVERT_HANDLERS: dict[str, _Handler] = {
    "create_task": _revert_create_task,
    "update_task": _revert_update_task,
    "delete_task": _revert_delete_task,
    "complete_task": _revert_complete_task,
    "set_daily_plan": _revert_set_daily_plan,
    "mark_day_off": _revert_mark_day_off,
    "unmark_day_off": _revert_unmark_day_off,
    "set_recurring_days_off": _revert_set_recurring_days_off,
    "set_day_metadata": _revert_set_day_metadata,
    "notify": _revert_notify,
    "start_timer": _revert_start_timer,
    "stop_timer": _revert_stop_timer,
}


class MCPLogService:
    """Encapsulates all MCP log read and revert operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_logs(self, limit: int = 50, offset: int = 0) -> list[MCPLog]:
        result = await self._db.execute(
            select(MCPLog)
            .order_by(MCPLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def revert(self, log_id: int) -> MCPLog:
        result = await self._db.execute(
            select(MCPLog).where(MCPLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        if log is None:
            raise ValueError(f"Log entry {log_id} not found")
        if log.is_reverted:
            raise ValueError("Already reverted")
        if log.status != "success":
            raise ValueError("Cannot revert a failed tool call")
        handler = REVERT_HANDLERS.get(log.tool_name)
        if not handler:
            raise ValueError(f"No revert handler for '{log.tool_name}'")
        await handler(self._db, log)
        log.is_reverted = True
        await self._db.commit()
        await self._db.refresh(log)
        return log
