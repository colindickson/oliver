# Recurring Tasks from Templates — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow task templates to be scheduled on a recurring basis (weekly, bi-weekly, monthly); tasks auto-appear when the user opens any due day.

**Architecture:** A new `template_schedules` table stores recurrence rules. Each schedule has a `next_run_date` cursor that advances forward after each evaluation. When any day is opened (`GET /api/days/today` or `GET /api/days/{date}`), the backend checks all schedules with `next_run_date <= target_date`, instantiates tasks for non-off-days, and advances the cursor — no background jobs required.

**Tech Stack:** FastAPI, SQLAlchemy async (asyncpg in prod, aiosqlite in tests), Alembic, pytest-asyncio + httpx for integration tests, React + TypeScript + TanStack Query on the frontend.

---

## Task 1: Add `TemplateSchedule` ORM model

**Files:**
- Modify: `backend/app/models/task_template.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_templates.py` (in a new section at the bottom):

```python
# ---------------------------------------------------------------------------
# TemplateSchedule model existence
# ---------------------------------------------------------------------------

async def test_schedule_model_fields(db_session: AsyncSession) -> None:
    """TemplateSchedule can be created with required fields."""
    from app.models.task_template import TemplateSchedule
    from datetime import date

    template = TaskTemplate(title="Yoga")
    db_session.add(template)
    await db_session.flush()

    schedule = TemplateSchedule(
        template_id=template.id,
        recurrence="weekly",
        anchor_date=date(2026, 3, 3),
        next_run_date=date(2026, 3, 3),
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)

    assert schedule.id is not None
    assert schedule.recurrence == "weekly"
    assert schedule.anchor_date == date(2026, 3, 3)
    assert schedule.next_run_date == date(2026, 3, 3)
```

Also add `from app.models.task_template import TaskTemplate` to the test file imports if not already present.

**Step 2: Run test to verify it fails**

```bash
docker compose exec backend pytest tests/test_templates.py::test_schedule_model_fields -v
```
Expected: FAIL — `ImportError: cannot import name 'TemplateSchedule'`

**Step 3: Add `TemplateSchedule` model to `backend/app/models/task_template.py`**

Append after the existing `TaskTemplate` class:

```python
from datetime import date as date_type  # add at top of file imports


class TemplateSchedule(Base):
    """A recurring schedule attached to a TaskTemplate."""

    __tablename__ = "template_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("task_templates.id", ondelete="CASCADE"), nullable=False
    )
    recurrence: Mapped[str] = mapped_column(String(20), nullable=False)  # weekly | bi_weekly | monthly
    anchor_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    next_run_date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    template: Mapped[TaskTemplate] = relationship("TaskTemplate", back_populates="schedules")
```

Also add the `Date` import to the existing SQLAlchemy imports line:
```python
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table
```

And add back-reference on `TaskTemplate`:
```python
schedules: Mapped[list["TemplateSchedule"]] = relationship(
    "TemplateSchedule",
    back_populates="template",
    cascade="all, delete-orphan",
    lazy="selectin",
)
```

**Step 4: Register in `backend/app/models/__init__.py`**

Open the file and add `TemplateSchedule` to the imports so SQLAlchemy registers the table:
```python
from app.models.task_template import TaskTemplate, TemplateSchedule  # noqa: F401
```

**Step 5: Run test to verify it passes**

```bash
docker compose exec backend pytest tests/test_templates.py::test_schedule_model_fields -v
```
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/models/task_template.py backend/app/models/__init__.py backend/tests/test_templates.py
git commit -m "Add TemplateSchedule ORM model"
```

---

## Task 2: Alembic migration for `template_schedules`

**Files:**
- Create: `backend/alembic/versions/<hash>_add_template_schedules.py`

**Step 1: Generate the migration**

```bash
docker compose exec backend alembic revision --autogenerate -m "add_template_schedules"
```

A new file appears in `backend/alembic/versions/`. Open it and verify the `upgrade()` function creates the `template_schedules` table. It should look roughly like:

```python
def upgrade() -> None:
    op.create_table(
        'template_schedules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('recurrence', sa.String(length=20), nullable=False),
        sa.Column('anchor_date', sa.Date(), nullable=False),
        sa.Column('next_run_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['task_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_template_schedules_next_run_date'), 'template_schedules', ['next_run_date'], unique=False)
```

If autogenerate missed anything, add it manually.

**Step 2: Run the migration**

```bash
docker compose exec backend alembic upgrade head
```
Expected: `Running upgrade 8108a2a45bc3 -> <new_hash>, add_template_schedules`

**Step 3: Verify migration status**

```bash
docker compose exec backend alembic current
```
Expected: new revision hash with `(head)`

**Step 4: Commit**

```bash
git add backend/alembic/versions/
git commit -m "Add migration for template_schedules table"
```

---

## Task 3: Pydantic schemas for TemplateSchedule

**Files:**
- Modify: `backend/app/schemas/task_template.py`

**Step 1: No test needed** — schemas are validated implicitly by API tests. Skip to implementation.

**Step 2: Add schemas**

Append to `backend/app/schemas/task_template.py`:

```python
from datetime import date as date_type
from typing import Literal

RecurrenceType = Literal["weekly", "bi_weekly", "monthly"]


class ScheduleCreate(BaseModel):
    recurrence: RecurrenceType
    anchor_date: date_type


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    recurrence: str
    anchor_date: date_type
    next_run_date: date_type
    created_at: datetime
```

**Step 3: Commit**

```bash
git add backend/app/schemas/task_template.py
git commit -m "Add ScheduleCreate and ScheduleResponse schemas"
```

---

## Task 4: `compute_next_run` utility + tests

**Files:**
- Modify: `backend/app/services/template_service.py`
- Modify: `backend/tests/test_templates.py`

**Step 1: Write the failing tests**

Add to `backend/tests/test_templates.py`:

```python
# ---------------------------------------------------------------------------
# compute_next_run utility
# ---------------------------------------------------------------------------

from datetime import date as _date
from app.services.template_service import compute_next_run


def test_compute_next_run_weekly():
    assert compute_next_run(_date(2026, 3, 2), "weekly") == _date(2026, 3, 9)


def test_compute_next_run_bi_weekly():
    assert compute_next_run(_date(2026, 3, 2), "bi_weekly") == _date(2026, 3, 16)


def test_compute_next_run_monthly():
    assert compute_next_run(_date(2026, 1, 31), "monthly") == _date(2026, 2, 28)


def test_compute_next_run_monthly_normal():
    assert compute_next_run(_date(2026, 3, 15), "monthly") == _date(2026, 4, 15)
```

**Step 2: Run to verify failure**

```bash
docker compose exec backend pytest tests/test_templates.py::test_compute_next_run_weekly tests/test_templates.py::test_compute_next_run_bi_weekly tests/test_templates.py::test_compute_next_run_monthly tests/test_templates.py::test_compute_next_run_monthly_normal -v
```
Expected: FAIL — `ImportError: cannot import name 'compute_next_run'`

**Step 3: Implement `compute_next_run` in `template_service.py`**

Add this module-level function (not a method) at the top of `backend/app/services/template_service.py`, after the imports:

```python
from calendar import monthrange
from datetime import date as date_type, timedelta


def compute_next_run(current: date_type, recurrence: str) -> date_type:
    """Return the next occurrence date given the current date and recurrence type."""
    if recurrence == "weekly":
        return current + timedelta(days=7)
    if recurrence == "bi_weekly":
        return current + timedelta(days=14)
    # monthly: same day next month, clamped to last day of month
    month = current.month % 12 + 1
    year = current.year + (current.month // 12)
    max_day = monthrange(year, month)[1]
    return date_type(year, month, min(current.day, max_day))
    raise ValueError(f"Unknown recurrence: {recurrence}")
```

**Step 4: Run tests to verify they pass**

```bash
docker compose exec backend pytest tests/test_templates.py::test_compute_next_run_weekly tests/test_templates.py::test_compute_next_run_bi_weekly tests/test_templates.py::test_compute_next_run_monthly tests/test_templates.py::test_compute_next_run_monthly_normal -v
```
Expected: 4 PASS

**Step 5: Commit**

```bash
git add backend/app/services/template_service.py backend/tests/test_templates.py
git commit -m "Add compute_next_run utility for weekly/bi-weekly/monthly recurrence"
```

---

## Task 5: Schedule CRUD in `TemplateService`

**Files:**
- Modify: `backend/app/services/template_service.py`
- Modify: `backend/tests/test_templates.py`

**Step 1: Write the failing tests**

Add to `backend/tests/test_templates.py`:

```python
# ---------------------------------------------------------------------------
# Schedule CRUD API endpoints
# ---------------------------------------------------------------------------


async def test_create_schedule(client: AsyncClient) -> None:
    """POST /api/templates/{id}/schedules creates a schedule."""
    template = (await client.post("/api/templates", json={"title": "Yoga"})).json()

    response = await client.post(
        f"/api/templates/{template['id']}/schedules",
        json={"recurrence": "weekly", "anchor_date": "2026-03-03"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["recurrence"] == "weekly"
    assert body["anchor_date"] == "2026-03-03"
    assert body["next_run_date"] == "2026-03-03"
    assert body["template_id"] == template["id"]
    assert "id" in body


async def test_create_schedule_invalid_recurrence(client: AsyncClient) -> None:
    """POST /api/templates/{id}/schedules with bad recurrence returns 422."""
    template = (await client.post("/api/templates", json={"title": "Yoga"})).json()

    response = await client.post(
        f"/api/templates/{template['id']}/schedules",
        json={"recurrence": "daily", "anchor_date": "2026-03-03"},
    )

    assert response.status_code == 422


async def test_list_schedules(client: AsyncClient) -> None:
    """GET /api/templates/{id}/schedules lists all schedules for a template."""
    template = (await client.post("/api/templates", json={"title": "Yoga"})).json()
    await client.post(
        f"/api/templates/{template['id']}/schedules",
        json={"recurrence": "weekly", "anchor_date": "2026-03-03"},
    )
    await client.post(
        f"/api/templates/{template['id']}/schedules",
        json={"recurrence": "monthly", "anchor_date": "2026-03-03"},
    )

    response = await client.get(f"/api/templates/{template['id']}/schedules")

    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_schedules_empty(client: AsyncClient) -> None:
    """GET /api/templates/{id}/schedules returns [] when none exist."""
    template = (await client.post("/api/templates", json={"title": "Empty"})).json()

    response = await client.get(f"/api/templates/{template['id']}/schedules")

    assert response.status_code == 200
    assert response.json() == []


async def test_delete_schedule(client: AsyncClient) -> None:
    """DELETE /api/templates/{id}/schedules/{sid} removes the schedule."""
    template = (await client.post("/api/templates", json={"title": "Yoga"})).json()
    schedule = (await client.post(
        f"/api/templates/{template['id']}/schedules",
        json={"recurrence": "weekly", "anchor_date": "2026-03-03"},
    )).json()

    del_resp = await client.delete(
        f"/api/templates/{template['id']}/schedules/{schedule['id']}"
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

    list_resp = await client.get(f"/api/templates/{template['id']}/schedules")
    assert list_resp.json() == []


async def test_delete_schedule_not_found(client: AsyncClient) -> None:
    """DELETE /api/templates/1/schedules/9999 returns 404."""
    template = (await client.post("/api/templates", json={"title": "Yoga"})).json()

    response = await client.delete(
        f"/api/templates/{template['id']}/schedules/9999"
    )
    assert response.status_code == 404
```

**Step 2: Run to verify failure**

```bash
docker compose exec backend pytest tests/test_templates.py::test_create_schedule tests/test_templates.py::test_list_schedules -v
```
Expected: FAIL — 404 (routes don't exist yet)

**Step 3: Add service methods to `TemplateService`**

Add to `backend/app/services/template_service.py` inside the `TemplateService` class:

```python
from datetime import date as date_type  # add to imports at top

async def list_schedules(self, template_id: int) -> list["TemplateSchedule"]:
    """Return all schedules for a template."""
    from app.models.task_template import TemplateSchedule
    result = await self._db.execute(
        select(TemplateSchedule).where(TemplateSchedule.template_id == template_id)
    )
    return list(result.scalars().all())

async def create_schedule(
    self,
    template_id: int,
    recurrence: str,
    anchor_date: date_type,
) -> "TemplateSchedule":
    """Create a new recurrence schedule for a template."""
    from app.models.task_template import TemplateSchedule
    schedule = TemplateSchedule(
        template_id=template_id,
        recurrence=recurrence,
        anchor_date=anchor_date,
        next_run_date=anchor_date,
    )
    self._db.add(schedule)
    await self._db.commit()
    await self._db.refresh(schedule)
    return schedule

async def delete_schedule(self, template_id: int, schedule_id: int) -> bool:
    """Delete a schedule by ID. Returns True if found and deleted."""
    from app.models.task_template import TemplateSchedule
    schedule = await self._db.scalar(
        select(TemplateSchedule).where(
            TemplateSchedule.id == schedule_id,
            TemplateSchedule.template_id == template_id,
        )
    )
    if schedule is None:
        return False
    await self._db.delete(schedule)
    await self._db.commit()
    return True
```

**Step 4: Add API routes to `backend/app/api/templates.py`**

Add these three routes at the end of the file:

```python
from app.schemas.task_template import ScheduleCreate, ScheduleResponse  # add to existing import


@router.get("/{template_id}/schedules", response_model=list[ScheduleResponse])
async def list_schedules(
    template_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[ScheduleResponse]:
    """List all recurrence schedules for a template."""
    service = TemplateService(db)
    await _get_template_or_404(template_id, service)
    return await service.list_schedules(template_id)


@router.post("/{template_id}/schedules", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    template_id: int,
    body: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
) -> ScheduleResponse:
    """Create a new recurrence schedule for a template."""
    service = TemplateService(db)
    await _get_template_or_404(template_id, service)
    return await service.create_schedule(
        template_id=template_id,
        recurrence=body.recurrence,
        anchor_date=body.anchor_date,
    )


@router.delete("/{template_id}/schedules/{schedule_id}")
async def delete_schedule(
    template_id: int,
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Delete a recurrence schedule."""
    service = TemplateService(db)
    await _get_template_or_404(template_id, service)
    deleted = await service.delete_schedule(template_id, schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"deleted": True}
```

**Step 5: Run all schedule tests**

```bash
docker compose exec backend pytest tests/test_templates.py::test_create_schedule tests/test_templates.py::test_create_schedule_invalid_recurrence tests/test_templates.py::test_list_schedules tests/test_templates.py::test_list_schedules_empty tests/test_templates.py::test_delete_schedule tests/test_templates.py::test_delete_schedule_not_found -v
```
Expected: 6 PASS

**Step 6: Commit**

```bash
git add backend/app/services/template_service.py backend/app/api/templates.py backend/tests/test_templates.py
git commit -m "Add schedule CRUD endpoints and service methods"
```

---

## Task 6: `apply_due_schedules` in `DayService`

This is the core logic: when a day is opened, fire any due schedules.

**Files:**
- Modify: `backend/app/services/day_service.py`
- Create: `backend/tests/test_schedule_application.py`

**Step 1: Write the failing tests**

Create `backend/tests/test_schedule_application.py`:

```python
"""Integration tests for recurring schedule application on day open."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.main import app
from app.database import Base, get_db
from app.models import Day, Task  # noqa: F401
from app.models.task_template import TaskTemplate, TemplateSchedule  # noqa: F401
from app.models.day_off import DayOff  # noqa: F401

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


async def _make_template_with_schedule(
    db: AsyncSession,
    recurrence: str,
    next_run_date: date,
    category: str = "short_task",
) -> TemplateSchedule:
    """Helper: insert a template + schedule directly into DB."""
    template = TaskTemplate(title="Yoga", category=category)
    db.add(template)
    await db.flush()
    schedule = TemplateSchedule(
        template_id=template.id,
        recurrence=recurrence,
        anchor_date=next_run_date,
        next_run_date=next_run_date,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def test_schedule_due_today_creates_task(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Opening a day with a due schedule auto-creates the task."""
    today = date.today()
    schedule = await _make_template_with_schedule(db_session, "weekly", today)

    response = await client.get(f"/api/days/{today.isoformat()}")

    assert response.status_code == 200
    tasks = response.json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Yoga"

    # next_run_date should have advanced by 7 days
    await db_session.refresh(schedule)
    from datetime import timedelta
    assert schedule.next_run_date == today + timedelta(days=7)


async def test_schedule_due_today_on_day_off_skips_task(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Opening a day-off with a due schedule does NOT create the task but still advances."""
    today = date.today()
    schedule = await _make_template_with_schedule(db_session, "weekly", today)

    # Mark today as a day off
    day_resp = await client.get(f"/api/days/{today.isoformat()}")
    day_id = day_resp.json()["id"]
    await client.put(f"/api/days/{day_id}/day-off", json={"reason": "personal_day"})

    # Open the day again (schedule was already applied once in first GET)
    # Reset next_run_date to today to simulate fresh state
    schedule.next_run_date = today
    await db_session.commit()

    response = await client.get(f"/api/days/{today.isoformat()}")
    tasks = response.json()["tasks"]
    assert len(tasks) == 0  # no task created

    await db_session.refresh(schedule)
    from datetime import timedelta
    assert schedule.next_run_date == today + timedelta(days=7)  # still advanced


async def test_schedule_future_not_applied(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A schedule with next_run_date in the future is not applied."""
    from datetime import timedelta
    future = date.today() + timedelta(days=3)
    await _make_template_with_schedule(db_session, "weekly", future)

    response = await client.get(f"/api/days/{date.today().isoformat()}")
    assert response.json()["tasks"] == []


async def test_schedule_missed_advances_without_creating_task(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A schedule due in the past advances to future without creating a task on today."""
    from datetime import timedelta
    past = date.today() - timedelta(days=3)
    today = date.today()
    schedule = await _make_template_with_schedule(db_session, "weekly", past)

    response = await client.get(f"/api/days/{today.isoformat()}")
    # past date ≠ today, so no task is created for today
    assert response.json()["tasks"] == []

    await db_session.refresh(schedule)
    # next_run_date should now be past the past date
    assert schedule.next_run_date > today


async def test_schedule_idempotent(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Opening the same day twice does not double-create tasks."""
    today = date.today()
    await _make_template_with_schedule(db_session, "weekly", today)

    await client.get(f"/api/days/{today.isoformat()}")
    response = await client.get(f"/api/days/{today.isoformat()}")

    assert len(response.json()["tasks"]) == 1
```

**Step 2: Run to verify failure**

```bash
docker compose exec backend pytest tests/test_schedule_application.py -v
```
Expected: FAIL — schedules are not applied yet (tasks list is empty when it shouldn't be)

**Step 3: Implement `apply_due_schedules` in `DayService`**

Add this method to `DayService` in `backend/app/services/day_service.py`:

```python
# add these imports at the top
from datetime import date as date_type
from calendar import monthrange

from app.models.task_template import TemplateSchedule, TaskTemplate
from app.services.template_service import compute_next_run, TemplateService


async def apply_due_schedules(self, day: Day, target_date: date_type) -> None:
    """Check all schedules with next_run_date <= target_date and apply them.

    For each due schedule:
    - If next_run_date == target_date AND day is not a day off: instantiate task
    - Always advance next_run_date past target_date
    """
    is_day_off = day.day_off is not None

    result = await self._db.execute(
        select(TemplateSchedule).where(TemplateSchedule.next_run_date <= target_date)
    )
    schedules = list(result.scalars().all())

    template_service = TemplateService(self._db)

    for schedule in schedules:
        if schedule.next_run_date == target_date and not is_day_off:
            template = await self._db.get(TaskTemplate, schedule.template_id)
            if template and template.category:
                await template_service.instantiate(
                    template=template,
                    day_id=day.id,
                    category_override=None,
                )

        # Advance next_run_date until it is past target_date
        while schedule.next_run_date <= target_date:
            schedule.next_run_date = compute_next_run(
                schedule.next_run_date, schedule.recurrence
            )

    if schedules:
        await self._db.commit()
```

**Step 4: Call `apply_due_schedules` from `get_or_create_by_date`**

In `DayService.get_or_create_by_date`, add the schedule application call at the end, after the day is fetched/created:

```python
async def get_or_create_by_date(self, target_date: date) -> Day:
    result = await self._db.execute(select(Day).where(Day.date == target_date))
    day = result.scalar_one_or_none()
    if day is None:
        day = Day(date=target_date, created_at=datetime.now(timezone.utc))
        self._db.add(day)
        await self._db.flush()
        await self._db.refresh(day)

    await self.apply_due_schedules(day, target_date)  # <-- add this line
    return day
```

**Step 5: Run tests**

```bash
docker compose exec backend pytest tests/test_schedule_application.py -v
```
Expected: 5 PASS

**Step 6: Run full test suite to check for regressions**

```bash
docker compose exec backend pytest -v
```
Expected: all passing

**Step 7: Commit**

```bash
git add backend/app/services/day_service.py backend/tests/test_schedule_application.py
git commit -m "Apply due schedules when opening a day"
```

---

## Task 7: Frontend — `client.ts` schedule API additions

**Files:**
- Modify: `frontend/src/api/client.ts`

**Step 1: No automated test** — API client additions are covered by component integration. Proceed directly.

**Step 2: Add types and API methods**

In `frontend/src/api/client.ts`, append after the existing `templatesApi` block:

```typescript
export type RecurrenceType = 'weekly' | 'bi_weekly' | 'monthly'

export interface TemplateSchedule {
  id: number
  template_id: number
  recurrence: RecurrenceType
  anchor_date: string   // ISO date string
  next_run_date: string // ISO date string
  created_at: string
}
```

Then extend `templatesApi` (add to the existing object):

```typescript
export const templatesApi = {
  // ... existing methods ...
  listSchedules: (templateId: number) =>
    api.get<TemplateSchedule[]>(`/templates/${templateId}/schedules`).then(r => r.data),
  createSchedule: (templateId: number, payload: { recurrence: RecurrenceType; anchor_date: string }) =>
    api.post<TemplateSchedule>(`/templates/${templateId}/schedules`, payload).then(r => r.data),
  deleteSchedule: (templateId: number, scheduleId: number) =>
    api.delete(`/templates/${templateId}/schedules/${scheduleId}`).then(r => r.data),
}
```

**Step 3: Commit**

```bash
git add frontend/src/api/client.ts
git commit -m "Add TemplateSchedule types and schedule API methods to client.ts"
```

---

## Task 8: `ScheduleModal` component

**Files:**
- Create: `frontend/src/components/ScheduleModal.tsx`

**Step 1: Create the component**

Create `frontend/src/components/ScheduleModal.tsx`:

```tsx
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { templatesApi, type TaskTemplate, type RecurrenceType } from '../api/client'

const RECURRENCE_LABELS: Record<RecurrenceType, string> = {
  weekly: 'Weekly',
  bi_weekly: 'Bi-weekly',
  monthly: 'Monthly',
}

function tomorrow(): string {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
}

interface Props {
  template: TaskTemplate
  onClose: () => void
}

export function ScheduleModal({ template, onClose }: Props) {
  const qc = useQueryClient()
  const [recurrence, setRecurrence] = useState<RecurrenceType>('weekly')
  const [anchorDate, setAnchorDate] = useState(tomorrow())
  const [error, setError] = useState('')

  const { data: schedules = [], isLoading } = useQuery({
    queryKey: ['schedules', template.id],
    queryFn: () => templatesApi.listSchedules(template.id),
  })

  const create = useMutation({
    mutationFn: () =>
      templatesApi.createSchedule(template.id, { recurrence, anchor_date: anchorDate }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['schedules', template.id] })
      qc.invalidateQueries({ queryKey: ['templates'] })
      setError('')
    },
    onError: () => setError('Failed to create schedule.'),
  })

  const remove = useMutation({
    mutationFn: (scheduleId: number) =>
      templatesApi.deleteSchedule(template.id, scheduleId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['schedules', template.id] })
      qc.invalidateQueries({ queryKey: ['templates'] })
    },
  })

  return (
    <div
      className="fixed inset-0 bg-stone-900/50 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="schedule-modal-title"
        className="bg-white rounded-2xl shadow-soft-lg p-6 w-full max-w-sm mx-4 animate-slide-up dark:bg-stone-700"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-moss-100 dark:bg-moss-900/30 flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-moss-600 dark:text-moss-400" aria-hidden="true">
              <circle cx="9" cy="9" r="7" />
              <path d="M9 5v4l2.5 2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div>
            <h2 id="schedule-modal-title" className="text-base font-semibold text-stone-800 dark:text-stone-100">
              Schedules
            </h2>
            <p className="text-xs text-stone-400 dark:text-stone-500 truncate max-w-[180px]">{template.title}</p>
          </div>
          <button
            onClick={onClose}
            className="ml-auto w-7 h-7 flex items-center justify-center rounded-lg text-stone-400 hover:text-stone-600 hover:bg-stone-100 dark:hover:text-stone-200 dark:hover:bg-stone-600 transition-colors"
            aria-label="Close"
          >
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
              <path d="M2 2l9 9M11 2l-9 9" />
            </svg>
          </button>
        </div>

        {/* Existing schedules */}
        <div className="mb-4">
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2].map(i => (
                <div key={i} className="h-10 rounded-xl bg-stone-100 dark:bg-stone-600/40 animate-pulse" />
              ))}
            </div>
          ) : schedules.length === 0 ? (
            <p className="text-sm text-stone-400 dark:text-stone-500 text-center py-3">
              No schedules yet.
            </p>
          ) : (
            <div className="space-y-1.5">
              {schedules.map(s => (
                <div key={s.id} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-stone-50 dark:bg-stone-800/60 border border-stone-100 dark:border-stone-600/40">
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-stone-700 dark:text-stone-200">
                      {RECURRENCE_LABELS[s.recurrence as RecurrenceType]}
                    </span>
                    <span className="text-xs text-stone-400 dark:text-stone-500 ml-2">
                      starting {s.anchor_date}
                    </span>
                    <div className="text-xs text-stone-400 dark:text-stone-500">
                      next: {s.next_run_date}
                    </div>
                  </div>
                  <button
                    onClick={() => remove.mutate(s.id)}
                    disabled={remove.isPending}
                    className="w-6 h-6 flex items-center justify-center rounded-lg text-stone-300 hover:text-terracotta-500 hover:bg-terracotta-50 dark:hover:text-terracotta-400 dark:hover:bg-terracotta-900/20 transition-colors"
                    aria-label="Delete schedule"
                  >
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" aria-hidden="true">
                      <path d="M2 2l8 8M10 2l-8 8" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="border-t border-stone-100 dark:border-stone-600 mb-4" />

        {/* Add schedule form */}
        <div className="space-y-3">
          <p className="text-xs font-medium text-stone-500 dark:text-stone-400 uppercase tracking-wider">Add schedule</p>

          <div className="flex gap-2">
            <select
              value={recurrence}
              onChange={e => setRecurrence(e.target.value as RecurrenceType)}
              className="flex-1 text-sm border border-stone-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-moss-300 focus:border-transparent transition-shadow dark:bg-stone-800 dark:border-stone-600 dark:text-stone-100"
            >
              {(Object.keys(RECURRENCE_LABELS) as RecurrenceType[]).map(r => (
                <option key={r} value={r}>{RECURRENCE_LABELS[r]}</option>
              ))}
            </select>
            <input
              type="date"
              value={anchorDate}
              onChange={e => setAnchorDate(e.target.value)}
              className="flex-1 text-sm border border-stone-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-moss-300 focus:border-transparent transition-shadow dark:bg-stone-800 dark:border-stone-600 dark:text-stone-100 dark:[color-scheme:dark]"
            />
          </div>

          {error && <p className="text-xs text-terracotta-600 dark:text-terracotta-400">{error}</p>}

          <button
            onClick={() => create.mutate()}
            disabled={create.isPending || !anchorDate}
            className="w-full text-sm bg-stone-800 text-white rounded-lg px-4 py-2 hover:bg-stone-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all dark:bg-stone-600 dark:hover:bg-stone-500"
          >
            {create.isPending ? 'Adding…' : 'Add'}
          </button>
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/ScheduleModal.tsx
git commit -m "Add ScheduleModal component"
```

---

## Task 9: Wire `ScheduleModal` into Settings page

**Files:**
- Modify: `frontend/src/pages/Settings.tsx`

**Step 1: Add state and imports**

At the top of `Settings.tsx`, add the import:
```tsx
import { ScheduleModal } from '../components/ScheduleModal'
```

Inside the `Settings()` function, add state for the schedule modal alongside the existing template state:
```tsx
const [schedulingTemplate, setSchedulingTemplate] = useState<TaskTemplate | null>(null)
```

**Step 2: Add the schedule count query**

Add this query inside the `Settings()` function:
```tsx
// Fetch schedule counts for each template so we can show the badge
const { data: allSchedules = {} } = useQuery({
  queryKey: ['all-schedules', templates.map(t => t.id)],
  queryFn: async () => {
    const results = await Promise.all(
      templates.map(t => templatesApi.listSchedules(t.id).then(s => [t.id, s.length] as const))
    )
    return Object.fromEntries(results)
  },
  enabled: templates.length > 0,
})
```

**Step 3: Add the schedule button to each template row**

In the template row's "Hover actions" `div` (currently contains edit + delete buttons), add a schedule button **before** the edit button:

```tsx
<button
  type="button"
  onClick={() => setSchedulingTemplate(t)}
  className="w-7 h-7 flex items-center justify-center rounded-lg text-stone-400 hover:text-moss-600 hover:bg-moss-50 dark:hover:text-moss-400 dark:hover:bg-moss-900/20 transition-colors relative"
  aria-label={`Schedules for ${t.title}`}
>
  <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
    <circle cx="6.5" cy="6.5" r="5" />
    <path d="M6.5 4v2.5l1.5 1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
  {(allSchedules[t.id] ?? 0) > 0 && (
    <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-moss-500 text-white text-[8px] font-bold flex items-center justify-center">
      {allSchedules[t.id]}
    </span>
  )}
</button>
```

**Step 4: Render the ScheduleModal**

At the bottom of the return, alongside the existing `TemplateModal`, add:

```tsx
{schedulingTemplate && (
  <ScheduleModal
    template={schedulingTemplate}
    onClose={() => setSchedulingTemplate(null)}
  />
)}
```

**Step 5: Manual verification**

1. Start the app: `make up && make dev-frontend`
2. Navigate to Settings
3. Create a template (e.g. "Yoga", category "Short Task")
4. Hover over the template row — clock icon should appear
5. Click the clock icon — ScheduleModal opens
6. Add a weekly schedule starting tomorrow — item appears in the list
7. Add a monthly schedule — second item appears
8. Badge on clock icon shows `2`
9. Delete one schedule — badge drops to `1`
10. Navigate to today's day — no yoga task (schedule is for tomorrow)
11. Create a schedule with today's date as `anchor_date` via the API directly or set it in the UI; open today's day — yoga task appears automatically

**Step 6: Commit**

```bash
git add frontend/src/pages/Settings.tsx
git commit -m "Wire ScheduleModal into Settings page with schedule count badge"
```

---

## Task 10: Final verification + branch

**Step 1: Run full backend test suite**

```bash
docker compose exec backend pytest -v
```
Expected: all tests pass

**Step 2: TypeScript check**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

**Step 3: Create feature branch and push**

```bash
git checkout -b feature/recurring-task-schedules
git push -u origin feature/recurring-task-schedules
```

**Step 4: Open PR**

```bash
gh pr create --title "Add recurring task schedules from templates" --body "$(cat <<'EOF'
## Summary
- New `template_schedules` table: recurrence type + anchor date + next_run_date cursor
- Auto-apply due schedules when any day is opened (lazy evaluation, no background jobs)
- Days off are skipped; missed occurrences advance without creating tasks (idempotent)
- Frontend: ScheduleModal with list/add/delete; schedule count badge on template rows

## Test plan
- [ ] Backend tests pass: `docker compose exec backend pytest -v`
- [ ] TypeScript compiles: `cd frontend && npx tsc --noEmit`
- [ ] Create yoga template, add weekly schedule, navigate to the scheduled day → task auto-appears
- [ ] Mark scheduled day as off, reset next_run_date via DB, re-open → no task created, cursor advances
- [ ] Open same day twice → only one task created (idempotency)
EOF
)"
```
