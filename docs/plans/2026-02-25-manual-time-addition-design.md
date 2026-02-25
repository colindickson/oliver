# Manual Time Addition Design

**Date:** 2026-02-25
**Feature:** +15m / +1h buttons to manually add time to today's deep work task

## Problem

Users sometimes forget to start the timer. They need a quick way to manually credit time to their deep work task without going through the full timer flow.

## Solution

Add two buttons (+15m, +1h) to the SidebarTimer that create a TimerSession record directly, without touching the active timer state machine.

## Backend

### New Endpoint

`POST /api/timer/add-time`

**Request:**
```json
{ "task_id": 123, "seconds": 900 }
```

**Behavior:**
- Creates a `TimerSession` record with:
  - `task_id` from request
  - `started_at`: `now - seconds`
  - `ended_at`: `now`
  - `duration_seconds`: `seconds`
- No interaction with active timer state
- Returns the created `TimerSessionResponse`

## Frontend

### `timerApi`
New `addTime(task_id, seconds)` function calling `POST /timer/add-time`.

### `useTimer` hook
New `addTime` mutation. On success, invalidates `['timer']`, `['sessions']`, and `['analytics']` query keys so DeepWorkProgress and session history update immediately.

### `SidebarTimer`
Two small buttons (+15m, +1h) rendered whenever a deep work task is identified (same condition as the Start button). Clicking calls `addTime` with the task's id and either 900 or 3600 seconds.

## Trade-offs

- **Chosen approach (create TimerSession directly):** Simple, auditable, no state machine interaction. Multiple session records per task is already supported.
- **Rejected (modify accumulated_seconds):** Mutates live timer state, complicates stop logic, inconsistent history.
