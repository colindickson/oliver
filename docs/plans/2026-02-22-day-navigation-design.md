# Day Navigation Design

**Date:** 2026-02-22

## Problem

The calendar currently only responds to clicks on days that already have recorded data. Future days and empty past days are non-interactive. The DayOverviewModal (shown on click) is read-only. There is no way to add tasks to future days for planning, or to edit tasks from past days.

## Solution Overview

Make every calendar day clickable, navigating directly to a fully editable DayDetail page. Remove the DayOverviewModal. Auto-create Day records on the backend so navigating to any date always succeeds.

## Approach Chosen

**Auto-create on navigate + edit in DayDetail.** Consistent with the existing `/today` pattern. Simplest frontend logic with no empty-state edge cases.

---

## Design Sections

### 1. Calendar Page

- Remove `selectedDay` state and all `DayOverviewModal` usage.
- Every calendar cell navigates to `/day/:date` on click, regardless of whether data exists for that date.
- Existing visual styling (color-coded completion rates, date numbers) is unchanged.
- Delete `DayOverviewModal` component file.

### 2. Backend

- Modify `GET /api/days/{date}` to use `get_or_create` instead of returning 404.
- `DayService` already has `get_or_create_today`; generalize it to accept an arbitrary date.
- No new endpoints. All callers receive a valid `DayResponse` for any date.

### 3. DayDetail Page — Editing

**Task completion toggling:**
- Completion circles become clickable buttons calling `taskApi` to toggle status (`todo` ↔ `completed`).
- React Query cache invalidated on success.
- On future dates: circles are non-interactive (no `onClick`, `cursor-default`, dimmed appearance, `title` tooltip explaining why).

**Add task form:**
- Each category section has an inline "Add task" row at the bottom.
- Clicking expands a title input; submitting calls `taskApi.create` with category and date, then collapses.
- Available on all dates (past, present, future) — planning ahead is allowed.

**Empty state:**
- `isError` block replaced with category sections showing only "Add task" rows — inviting blank slate.
- Auto-create means the page always loads a valid Day, so true errors are unexpected.

**Header:**
- Existing date heading unchanged.
- Future dates show a subtle "Planning" label for context.

### 4. Future-Date Enforcement

```ts
const todayStr = new Date().toISOString().slice(0, 10)
const isFuture = date > todayStr
```

| Capability | Past/Today | Future |
|---|---|---|
| View tasks | Yes | Yes |
| Add tasks | Yes | Yes |
| Complete tasks | Yes | No (dimmed, tooltip) |

---

## Files Affected

| File | Change |
|---|---|
| `frontend/src/pages/Calendar.tsx` | Remove modal state/handler, make all cells navigate |
| `frontend/src/components/DayOverviewModal.tsx` | Delete |
| `frontend/src/pages/DayDetail.tsx` | Add completion toggle, add-task form, future-date logic |
| `backend/app/api/days.py` | Change `get_day_by_date` to auto-create |
| `backend/app/services/day_service.py` | Generalize `get_or_create_today` to accept a date |
