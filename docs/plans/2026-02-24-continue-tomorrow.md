# Continue Tomorrow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "Continue Tomorrow" action to deep work tasks that marks the current task completed and creates a copy on tomorrow's day.

**Architecture:** Single new backend endpoint `POST /api/tasks/{task_id}/continue-tomorrow` handles both operations atomically. Frontend threads a new callback prop down through `TaskColumn` → `TaskCard`, showing the button only for `deep_work` tasks.

**Tech Stack:** FastAPI, async SQLAlchemy, React, TanStack Query, TypeScript

---

### Task 1: Backend — write failing tests

**Files:**
- Modify: `backend/tests/test_tasks.py`

**Step 1: Add the failing tests at the bottom of `backend/tests/test_tasks.py`**

Append these tests (they reference an endpoint that doesn't exist yet):

```python
# ---------------------------------------------------------------------------
# POST /api/tasks/{task_id}/continue-tomorrow
# ---------------------------------------------------------------------------


async def test_continue_tomorrow_marks_original_completed(
    client: AsyncClient, day: Day
) -> None:
    """continue-tomorrow sets the original task status to completed."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Deep focus block",
        "description": "Work on the thing",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    resp = await client.post(f"/api/tasks/{task_id}/continue-tomorrow")

    assert resp.status_code == 200
    # Verify original is now completed
    original_resp = await client.get(f"/api/tasks/{task_id}")
    assert original_resp.json()["status"] == STATUS_COMPLETED
    assert original_resp.json()["completed_at"] is not None


async def test_continue_tomorrow_creates_copy_on_next_day(
    client: AsyncClient, day: Day
) -> None:
    """continue-tomorrow returns a new pending deep_work task for tomorrow."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Deep focus block",
        "description": "Work on the thing",
        "order_index": 0,
    })
    task_id = create_resp.json()["id"]

    resp = await client.post(f"/api/tasks/{task_id}/continue-tomorrow")

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] != task_id
    assert body["title"] == "Deep focus block"
    assert body["description"] == "Work on the thing"
    assert body["category"] == CATEGORY_DEEP_WORK
    assert body["status"] == STATUS_PENDING
    assert body["completed_at"] is None


async def test_continue_tomorrow_copies_tags(
    client: AsyncClient, day: Day
) -> None:
    """continue-tomorrow carries tags over to the new task."""
    create_resp = await client.post("/api/tasks", json={
        "day_id": day.id,
        "category": CATEGORY_DEEP_WORK,
        "title": "Tagged task",
        "order_index": 0,
        "tags": ["focus", "project-x"],
    })
    task_id = create_resp.json()["id"]

    resp = await client.post(f"/api/tasks/{task_id}/continue-tomorrow")

    assert resp.status_code == 200
    assert sorted(resp.json()["tags"]) == ["focus", "project-x"]


async def test_continue_tomorrow_404_for_missing_task(
    client: AsyncClient,
) -> None:
    """continue-tomorrow returns 404 when the task does not exist."""
    resp = await client.post("/api/tasks/99999/continue-tomorrow")
    assert resp.status_code == 404
```

**Step 2: Run tests to verify they fail**

```bash
docker compose exec backend pytest tests/test_tasks.py::test_continue_tomorrow_marks_original_completed tests/test_tasks.py::test_continue_tomorrow_creates_copy_on_next_day tests/test_tasks.py::test_continue_tomorrow_copies_tags tests/test_tasks.py::test_continue_tomorrow_404_for_missing_task -v
```

Expected: 4 FAILs — `404 Not Found` or `405 Method Not Allowed` since the endpoint doesn't exist.

---

### Task 2: Backend — implement the endpoint

**Files:**
- Modify: `backend/app/api/tasks.py`

**Step 1: Add imports at the top of `backend/app/api/tasks.py`**

Add `timedelta` to the datetime import and import `DayService` and `CATEGORY_DEEP_WORK`, `STATUS_PENDING`:

```python
# Change this line:
from datetime import datetime, timezone
# To:
from datetime import date, datetime, timedelta, timezone
```

Add after the existing imports (after line 25):
```python
from app.services.day_service import DayService
from oliver_shared import CATEGORY_DEEP_WORK, STATUS_PENDING
```

**Step 2: Add the endpoint to `backend/app/api/tasks.py`**

Add this after the `move_task_to_backlog` endpoint (at the end of the file):

```python
@router.post("/{task_id}/continue-tomorrow", response_model=TaskResponse)
async def continue_task_tomorrow(
    task_id: int, db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """Mark a deep work task completed and create a copy on tomorrow's day.

    The original task is stamped completed. A new pending task is created
    for tomorrow with the same title, description, and tags.

    Args:
        task_id: Primary key of the Task to continue.
        db: Injected async database session.

    Returns:
        The newly created TaskResponse for tomorrow.

    Raises:
        HTTPException: 404 if no Task with ``task_id`` exists.
    """
    task = await _get_task_or_404(task_id, db)

    # Mark original completed
    task.status = STATUS_COMPLETED
    task.completed_at = datetime.now(timezone.utc)

    # Get or create tomorrow's Day
    tomorrow = date.today() + timedelta(days=1)
    day_service = DayService(db)
    tomorrow_day = await day_service.get_or_create_by_date(tomorrow)

    # Copy tags (tags are selectin-loaded, safe to read without extra query)
    tag_names = [tag.name for tag in task.tags]
    tag_objects = []
    if tag_names:
        tag_service = TagService(db)
        for name in tag_names:
            tag_objects.append(await tag_service.get_or_create_tag(name))

    # Create continuation task
    new_task = Task(
        day_id=tomorrow_day.id,
        category=CATEGORY_DEEP_WORK,
        title=task.title,
        description=task.description,
        status=STATUS_PENDING,
        order_index=0,
    )
    new_task.tags = tag_objects
    db.add(new_task)

    await db.commit()
    await db.refresh(new_task)
    return new_task
```

**Step 3: Run tests to verify they pass**

```bash
docker compose exec backend pytest tests/test_tasks.py::test_continue_tomorrow_marks_original_completed tests/test_tasks.py::test_continue_tomorrow_creates_copy_on_next_day tests/test_tasks.py::test_continue_tomorrow_copies_tags tests/test_tasks.py::test_continue_tomorrow_404_for_missing_task -v
```

Expected: 4 PASSes.

**Step 4: Run the full test suite to check for regressions**

```bash
docker compose exec backend pytest -v
```

Expected: all passing.

**Step 5: Commit**

```bash
git checkout -b feature/continue-tomorrow
git add backend/app/api/tasks.py backend/tests/test_tasks.py
git commit -m "feat: add continue-tomorrow endpoint for deep work tasks"
```

---

### Task 3: Frontend — API client method

**Files:**
- Modify: `frontend/src/api/client.ts`

**Step 1: Add `continueTomorrow` to `taskApi` in `frontend/src/api/client.ts`**

Find the `taskApi` object (around line 82). Add after the `moveToBacklog` entry:

```typescript
  continueTomorrow: (id: number) =>
    api.post<Task>(`/tasks/${id}/continue-tomorrow`).then(r => r.data),
```

The full `taskApi` block becomes:

```typescript
export const taskApi = {
  create: (payload: CreateTaskPayload) =>
    api.post<Task>('/tasks', payload).then(r => r.data),
  update: (id: number, payload: Partial<Pick<Task, 'title' | 'description'>> & { tags?: string[] }) =>
    api.put<Task>(`/tasks/${id}`, payload).then(r => r.data),
  delete: (id: number) =>
    api.delete(`/tasks/${id}`).then(r => r.data),
  setStatus: (id: number, status: Task['status']) =>
    api.patch<Task>(`/tasks/${id}/status`, { status }).then(r => r.data),
  reorder: (task_ids: number[]) =>
    api.post('/tasks/reorder', { task_ids }).then(r => r.data),
  moveToBacklog: (id: number) =>
    api.post<Task>(`/tasks/${id}/move-to-backlog`).then(r => r.data),
  continueTomorrow: (id: number) =>
    api.post<Task>(`/tasks/${id}/continue-tomorrow`).then(r => r.data),
}
```

**Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

**Step 3: Commit**

```bash
git add frontend/src/api/client.ts
git commit -m "feat: add continueTomorrow API client method"
```

---

### Task 4: Frontend — wire up the UI

**Files:**
- Modify: `frontend/src/pages/Today.tsx`
- Modify: `frontend/src/components/TaskColumn.tsx`
- Modify: `frontend/src/components/TaskCard.tsx`

**Step 1: Add the mutation and handler to `frontend/src/pages/Today.tsx`**

After the `moveToBacklog` mutation (around line 80), add:

```typescript
  const continueTomorrow = useMutation({
    mutationFn: taskApi.continueTomorrow,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['day', 'today'] }),
  })
```

After the `handleMoveToBacklog` function (around line 146), add:

```typescript
  function handleContinueTomorrow(task: Task) {
    continueTomorrow.mutate(task.id)
  }
```

In the JSX, add `onContinueTomorrow={handleContinueTomorrow}` to each `TaskColumn`:

```tsx
{columns.map(col => (
  <TaskColumn
    key={col.category}
    title={col.title}
    category={col.category}
    tasks={day.tasks}
    colorClass={col.color}
    onAddTask={(title, desc, tags) => handleAddTask(col.category, title, desc, tags)}
    onComplete={handleComplete}
    onDelete={handleDelete}
    onReorder={handleReorder}
    onMoveToBacklog={handleMoveToBacklog}
    onContinueTomorrow={handleContinueTomorrow}
    onScheduleFromBacklog={(task) => handleScheduleFromBacklog(task, col.category)}
  />
))}
```

**Step 2: Thread the prop through `frontend/src/components/TaskColumn.tsx`**

Add `onContinueTomorrow` to the `Props` interface (around line 24):

```typescript
interface Props {
  title: string
  category: Task['category']
  tasks: Task[]
  colorClass: ColorKey
  onAddTask: (title: string, description: string, tags: string[]) => Promise<void>
  onComplete: (task: Task) => void
  onDelete: (id: number) => void
  onReorder: (taskIds: number[]) => void
  onMoveToBacklog?: (task: Task) => void
  onContinueTomorrow?: (task: Task) => void
  onScheduleFromBacklog?: (task: Task) => void
}
```

Add `onContinueTomorrow` to the `SortableTaskCardProps` interface (around line 49):

```typescript
interface SortableTaskCardProps {
  task: Task
  onComplete: (task: Task) => void
  onDelete: (id: number) => void
  onMoveToBacklog?: (task: Task) => void
  onContinueTomorrow?: (task: Task) => void
}
```

Update the `SortableTaskCard` function signature and its internal `TaskCard` usage (around line 56):

```typescript
function SortableTaskCard({ task, onComplete, onDelete, onMoveToBacklog, onContinueTomorrow }: SortableTaskCardProps) {
  // ... existing drag handle code unchanged ...
  return (
    <div ref={setNodeRef} style={style} className="flex items-start gap-1">
      {/* Drag handle — unchanged */}
      <button
        type="button"
        className="mt-3 flex-shrink-0 text-stone-200 hover:text-stone-400 cursor-grab active:cursor-grabbing transition-colors px-0.5 dark:text-stone-600 dark:hover:text-stone-400"
        aria-label="Drag to reorder"
        {...attributes}
        {...listeners}
      >
        <svg width="10" height="16" viewBox="0 0 10 16" fill="currentColor">
          <circle cx="3" cy="3" r="1.5" />
          <circle cx="7" cy="3" r="1.5" />
          <circle cx="3" cy="8" r="1.5" />
          <circle cx="7" cy="8" r="1.5" />
          <circle cx="3" cy="13" r="1.5" />
          <circle cx="7" cy="13" r="1.5" />
        </svg>
      </button>
      <div className="flex-1 min-w-0">
        <TaskCard
          task={task}
          onComplete={onComplete}
          onDelete={onDelete}
          onMoveToBacklog={onMoveToBacklog}
          onContinueTomorrow={onContinueTomorrow}
        />
      </div>
    </div>
  )
}
```

Destructure the new prop in `TaskColumn` (around line 92) and pass it to `SortableTaskCard` (around line 210):

```typescript
export function TaskColumn({
  title,
  category,
  tasks,
  colorClass,
  onAddTask,
  onComplete,
  onDelete,
  onReorder,
  onMoveToBacklog,
  onContinueTomorrow,
  onScheduleFromBacklog,
}: Props) {
```

In the render loop (around line 209):

```tsx
{syncedTasks.map(task => (
  <SortableTaskCard
    key={task.id}
    task={task}
    onComplete={onComplete}
    onDelete={onDelete}
    onMoveToBacklog={onMoveToBacklog}
    onContinueTomorrow={onContinueTomorrow}
  />
))}
```

**Step 3: Add the button to `frontend/src/components/TaskCard.tsx`**

Add `onContinueTomorrow` to the `Props` interface (line 9):

```typescript
interface Props {
  task: Task
  onComplete: (task: Task) => void
  onDelete: (id: number) => void
  onMoveToBacklog?: (task: Task) => void
  onContinueTomorrow?: (task: Task) => void
}
```

Update the function signature (line 16):

```typescript
export function TaskCard({ task, onComplete, onDelete, onMoveToBacklog, onContinueTomorrow }: Props) {
```

Add the "Continue Tomorrow" button in the actions section, after the "Move to backlog" button and before "Delete" (around line 171). Only show it for deep_work tasks:

```tsx
          {/* Continue tomorrow — deep work only */}
          {onContinueTomorrow && task.category === 'deep_work' && (
            <button
              type="button"
              onClick={() => onContinueTomorrow(task)}
              className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-terracotta-400 hover:bg-terracotta-50 rounded transition-colors opacity-0 group-hover:opacity-100 dark:text-stone-600 dark:hover:text-terracotta-300 dark:hover:bg-stone-700"
              aria-label="Continue tomorrow"
              title="Continue tomorrow"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M7 2v5l3 2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 7a5 5 0 1 0 5-5" strokeLinecap="round" />
                <path d="M2 4V7h3" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          )}
```

**Step 4: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

**Step 5: Smoke test in the browser**

```bash
make up
```

Open http://localhost:5173, navigate to Today, hover over a deep work task. Verify:
- A "Continue tomorrow" icon button appears (clock/refresh icon)
- Clicking it marks the task completed (grays out with strikethrough)
- Short tasks and maintenance tasks do NOT show the button

**Step 6: Commit**

```bash
git add frontend/src/pages/Today.tsx frontend/src/components/TaskColumn.tsx frontend/src/components/TaskCard.tsx
git commit -m "feat: add Continue Tomorrow button to deep work TaskCard"
```
