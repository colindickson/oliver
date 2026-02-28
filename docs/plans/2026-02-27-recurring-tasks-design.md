# Recurring Tasks from Templates — Design

**Date:** 2026-02-27
**Status:** Approved

## Overview

Allow task templates to be scheduled on a recurring basis (weekly, bi-weekly, monthly). When a user opens a day, any due recurring tasks are automatically added to that day. Days marked as off are skipped — the next occurrence follows the normal schedule.

## Decisions

| Question | Decision |
|---|---|
| What happens on a day off? | Skip — next occurrence is the normal scheduled date |
| How do tasks appear? | Auto-added when the day is opened (lazy, request-driven) |
| Schedules per template | Multiple — same template can have independent recurrences |
| Creation mechanism | Option A: lazy evaluation on day open, no background jobs |

## Data Model

New table: **`template_schedules`**

| Column | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `template_id` | int FK → task_templates | CASCADE DELETE |
| `recurrence` | enum string | `weekly`, `bi_weekly`, `monthly` |
| `anchor_date` | date | Reference date; determines day-of-week (weekly/bi-weekly) or day-of-month (monthly) |
| `next_run_date` | date | Mutable cursor; indexed; starts as `anchor_date` |
| `created_at` | datetime | |

`anchor_date` is immutable and defines the pattern. `next_run_date` advances forward each time the schedule fires or is skipped.

## Backend Logic

### Schedule Application

Triggered inside `DayService.get_or_create_by_date()` after fetching/creating the Day row.

**Algorithm:**
1. Fetch all `TemplateSchedule` rows where `next_run_date <= target_date`
2. For each schedule:
   a. If `next_run_date == target_date` AND the day is **not** a day off → `template_service.instantiate(template, day_id)`
   b. Advance `next_run_date` to the next occurrence
   c. While `next_run_date <= target_date`: advance again (catches missed occurrences)
3. Commit all changes in one transaction

**Idempotency:** Once `next_run_date` advances past `target_date`, the schedule won't match that date again. Opening the same day multiple times is safe.

### Next-Occurrence Math

- `weekly` → `+ 7 days`
- `bi_weekly` → `+ 14 days`
- `monthly` → `+ 1 month` via `dateutil.relativedelta` (handles short months correctly)

### API Endpoints

All nested under `/api/templates/{template_id}/schedules`:

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/templates/{id}/schedules` | List all schedules for a template |
| `POST` | `/api/templates/{id}/schedules` | Create a new schedule (`{ recurrence, anchor_date }`) |
| `DELETE` | `/api/templates/{id}/schedules/{schedule_id}` | Delete a schedule |

### New Alembic Migration Required

Add `template_schedules` table with index on `next_run_date`.

## Frontend / UX

### Settings Page Changes

- Each template row in the list gains a small recurrence icon button
- If schedules exist, a count badge appears (e.g. `↻ 2`)
- Clicking opens the new `ScheduleModal`

### `ScheduleModal` Component (new)

- Header: "Schedules for [template name]"
- List of existing schedules: recurrence label + anchor date + next run date + delete (×) button
- Inline "Add schedule" form:
  - Recurrence selector: Weekly | Bi-weekly | Monthly
  - Start date picker (defaults to tomorrow)
  - "Add" button
- Visual style matches existing `TemplateModal`

### Day Views

No changes. Recurring tasks appear silently alongside regular tasks when a day is fetched.

### `client.ts` Additions

```ts
export type RecurrenceType = 'weekly' | 'bi_weekly' | 'monthly'

export interface TemplateSchedule {
  id: number
  template_id: number
  recurrence: RecurrenceType
  anchor_date: string
  next_run_date: string
  created_at: string
}

// Added to templatesApi:
listSchedules: (templateId: number) => Promise<TemplateSchedule[]>
createSchedule: (templateId: number, payload: { recurrence: RecurrenceType; anchor_date: string }) => Promise<TemplateSchedule>
deleteSchedule: (templateId: number, scheduleId: number) => Promise<void>
```

## Files to Touch

**Backend:**
- `backend/app/models/task_template.py` — add `TemplateSchedule` model
- `backend/app/schemas/task_template.py` — add `ScheduleCreate`, `ScheduleResponse`
- `backend/app/services/template_service.py` — add schedule CRUD methods
- `backend/app/services/day_service.py` — call `apply_due_schedules` in `get_or_create_by_date`
- `backend/app/api/templates.py` — add schedule endpoints
- `backend/alembic/versions/` — new migration

**Frontend:**
- `frontend/src/api/client.ts` — add `TemplateSchedule` type + `templatesApi` schedule methods
- `frontend/src/components/ScheduleModal.tsx` — new component
- `frontend/src/pages/Settings.tsx` — add schedule icon button to template rows

## Out of Scope

- Editing an existing schedule (delete + recreate instead)
- Retroactively adding tasks to past days
- Per-schedule category override (inherits from template)
- MCP server awareness of schedules
