# Continue Tomorrow — Design Doc

**Date:** 2026-02-24

## Overview

Add a "continue tomorrow" action to deep work tasks. Marks today's task as completed and creates a copy on tomorrow's day, representing ongoing work that carries forward.

## Behavior

- Only available on `deep_work` tasks
- Original task: marked `completed` with `completed_at` timestamp
- New task: same `title`, `description`, `tags`, `category=deep_work`, `status=pending`, assigned to tomorrow's Day
- Both operations are atomic (single database transaction)

## Backend

**New endpoint:** `POST /api/tasks/{task_id}/continue-tomorrow`

**New service method:** `continue_task_tomorrow(task_id, db)` in `task_service.py`

Steps:
1. Fetch task by `task_id`, return 404 if not found
2. Set `task.status = completed`, `task.completed_at = utcnow()`
3. Call `day_service.get_or_create_by_date(today + timedelta(days=1))` to get/create tomorrow's Day
4. Create new Task: same `title`, `description`, `tags`, `category=deep_work`, `status=pending`, `day_id=tomorrow.id`
5. Commit both changes in one transaction
6. Return the newly created task

## Frontend

**`client.ts`:** Add `continueTomorrow(id: number)` to `taskApi` — `POST /api/tasks/{id}/continue-tomorrow`

**`Today.tsx`:** Add `continueTomorrow` mutation; on success invalidate `['day', 'today']`

**`TaskCard.tsx`:** Add hover-visible icon button for "Continue Tomorrow", rendered only when `task.category === 'deep_work'`. Follows the same pattern as the existing "Move to Backlog" button.

## Out of Scope

- No visual indicator linking the original task to its copy
- No support for continuing tasks from the Backlog page
- Timer sessions and reminders are not copied
