# Day Navigation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make every calendar day clickable, navigating to a fully editable DayDetail page that supports adding tasks and toggling completion, with completion blocked on future dates.

**Architecture:** Backend auto-creates Day records on GET so the frontend never hits a 404. Calendar cells all navigate directly to `/day/:date`. DayDetail gains inline task creation and completion toggling, gated by a future-date check.

**Tech Stack:** FastAPI + SQLAlchemy (backend), React 18 + TypeScript + React Query + Tailwind (frontend)

---

### Task 1: Backend — auto-create Day on GET /api/days/{date}

**Files:**
- Modify: `backend/tests/test_days.py:108-113`
- Modify: `backend/app/api/days.py:36-56`

**Step 1: Update the test — replace 404 test with auto-create test**

In `backend/tests/test_days.py`, replace the existing `test_get_day_by_date_returns_404_when_missing` test (lines 108–113) with:

```python
async def test_get_day_by_date_auto_creates_when_missing(client: AsyncClient) -> None:
    """GET /api/days/{date} creates and returns the Day when none exists."""
    response = await client.get("/api/days/2030-06-15")

    assert response.status_code == 200
    payload = response.json()
    assert payload["date"] == "2030-06-15"
    assert "id" in payload
    assert isinstance(payload["tasks"], list)


async def test_get_day_by_date_auto_create_is_idempotent(client: AsyncClient) -> None:
    """GET /api/days/{date} called twice returns the same Day id."""
    r1 = await client.get("/api/days/2030-06-15")
    r2 = await client.get("/api/days/2030-06-15")

    assert r1.json()["id"] == r2.json()["id"]
```

**Step 2: Run the test to verify it fails**

```bash
cd /Users/colindickson/code/telex/oliver/backend && pytest tests/test_days.py::test_get_day_by_date_auto_creates_when_missing -v
```

Expected: FAIL with `assert 404 == 200`

**Step 3: Update the route in `backend/app/api/days.py`**

Replace the entire `get_day_by_date` function (lines 36–56) with:

```python
@router.get("/{day_date}", response_model=DayResponse)
async def get_day_by_date(
    day_date: date, db: AsyncSession = Depends(get_db)
) -> DayResponse:
    """Return the Day record for a specific calendar date, creating one if absent.

    Args:
        day_date: The date to look up, parsed from the URL path (YYYY-MM-DD).
        db: Injected async database session.

    Returns:
        The DayResponse for the requested date.
    """
    service = DayService(db)
    return await service.get_or_create_by_date(day_date)
```

Also remove the unused `HTTPException` import if it is no longer used anywhere else in the file. Check: if `HTTPException` only appeared in `get_day_by_date`, remove it from the import line. The import line currently reads:

```python
from fastapi import APIRouter, Depends, HTTPException
```

Change it to:

```python
from fastapi import APIRouter, Depends
```

**Step 4: Run all tests to verify they pass**

```bash
cd /Users/colindickson/code/telex/oliver/backend && pytest tests/test_days.py -v
```

Expected: All tests PASS. Note: the old `test_get_day_by_date_returns_404_when_missing` no longer exists — that's correct.

**Step 5: Commit**

```bash
cd /Users/colindickson/code/telex/oliver
git checkout -b feature/day-navigation
git add backend/app/api/days.py backend/tests/test_days.py
git commit -m "Auto-create Day on GET /api/days/{date}"
```

---

### Task 2: Calendar — remove modal, make all cells navigate

**Files:**
- Modify: `frontend/src/pages/Calendar.tsx`
- Delete: `frontend/src/components/DayOverviewModal.tsx`

**Step 1: Update Calendar.tsx**

Replace the entire contents of `frontend/src/pages/Calendar.tsx` with:

```tsx
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { dayApi } from '../api/client'
import type { Task } from '../api/client'
import { Sidebar } from '../components/Sidebar'
import { ExportModal } from '../components/ExportModal'

function getCompletionRate(tasks: Task[]): number {
  if (tasks.length === 0) return 0
  const completed = tasks.filter(t => t.status === 'completed').length
  return completed / tasks.length
}

export function Calendar() {
  const navigate = useNavigate()
  const [viewDate, setViewDate] = useState(new Date())
  const [showExportModal, setShowExportModal] = useState(false)

  const { data: days = [] } = useQuery({
    queryKey: ['days', 'all'],
    queryFn: dayApi.getAll,
  })

  const dayMap = new Map(days.map(d => [d.date, d]))

  const year = viewDate.getFullYear()
  const month = viewDate.getMonth()

  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startOffset = (firstDay.getDay() + 6) % 7
  const cells: Array<Date | null> = [
    ...Array(startOffset).fill(null),
    ...Array.from({ length: lastDay.getDate() }, (_, i) => new Date(year, month, i + 1)),
  ]
  while (cells.length % 7 !== 0) cells.push(null)

  const today = new Date()
  const todayStr = today.toISOString().slice(0, 10)

  const monthLabel = viewDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

  function prevMonth() {
    setViewDate(new Date(year, month - 1, 1))
  }
  function nextMonth() {
    setViewDate(new Date(year, month + 1, 1))
  }

  return (
    <div className="flex min-h-screen bg-stone-25">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-stone-200 px-8 py-5 flex items-center justify-between flex-shrink-0">
          <h1 className="text-xl font-semibold text-stone-800">Calendar</h1>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowExportModal(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-stone-600 bg-white border border-stone-200 rounded-xl hover:bg-stone-50 hover:border-stone-300 transition-all"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M8 2v8M5 7l3 3 3-3" />
                <path d="M2 12v1a1 1 0 001 1h10a1 1 0 001-1v-1" />
              </svg>
              Export
            </button>
            <p className="text-sm text-stone-400">{monthLabel}</p>
          </div>
        </header>

        {/* Calendar content */}
        <main className="flex-1 p-8">
          {/* Month navigation */}
          <div className="flex items-center justify-between mb-6 max-w-2xl">
            <button
              onClick={prevMonth}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-stone-600 bg-white border border-stone-200 rounded-xl hover:bg-stone-50 hover:border-stone-300 transition-all"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10 4L6 8L10 12" />
              </svg>
              Previous
            </button>

            <button
              onClick={() => setViewDate(new Date())}
              className="px-4 py-2 text-sm font-medium text-terracotta-600 bg-terracotta-50 rounded-xl hover:bg-terracotta-100 transition-colors"
            >
              Today
            </button>

            <button
              onClick={nextMonth}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-stone-600 bg-white border border-stone-200 rounded-xl hover:bg-stone-50 hover:border-stone-300 transition-all"
            >
              Next
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M6 4L10 8L6 12" />
              </svg>
            </button>
          </div>

          {/* Day headers */}
          <div className="grid grid-cols-7 gap-2 mb-2 max-w-2xl">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => (
              <div key={d} className="text-center text-xs font-medium text-stone-400 py-2">
                {d}
              </div>
            ))}
          </div>

          {/* Calendar grid */}
          <div className="grid grid-cols-7 gap-2 max-w-2xl">
            {cells.map((cellDate, i) => {
              if (!cellDate) return <div key={i} className="aspect-square" />

              const dateStr = cellDate.toISOString().slice(0, 10)
              const dayData = dayMap.get(dateStr)
              const tasks = dayData?.tasks ?? []
              const isToday = dateStr === todayStr
              const hasTasks = tasks.length > 0
              const completed = tasks.filter(t => t.status === 'completed').length
              const rate = getCompletionRate(tasks)

              let bgClass = 'bg-stone-50 text-stone-400 hover:bg-stone-100'
              if (hasTasks) {
                if (rate >= 1) bgClass = 'bg-moss-100 text-moss-700 hover:bg-moss-200'
                else if (rate >= 0.67) bgClass = 'bg-amber-50 text-amber-700 hover:bg-amber-100'
                else if (rate >= 0.33) bgClass = 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                else bgClass = 'bg-terracotta-50 text-terracotta-700 hover:bg-terracotta-100'
              }

              return (
                <button
                  key={dateStr}
                  onClick={() => navigate(`/day/${dateStr}`)}
                  className={`
                    aspect-square flex flex-col items-center justify-center rounded-xl text-sm font-medium
                    transition-all duration-200 cursor-pointer hover:shadow-soft hover:-translate-y-0.5
                    ${bgClass}
                    ${isToday ? 'ring-2 ring-terracotta-500 ring-offset-2' : ''}
                  `}
                >
                  <span>{cellDate.getDate()}</span>
                  {hasTasks && (
                    <span className="text-[10px] opacity-60 mt-0.5">
                      {completed}/{tasks.length}
                    </span>
                  )}
                </button>
              )
            })}
          </div>

          {/* Legend */}
          <div className="mt-8 flex items-center gap-6 text-xs text-stone-500 max-w-2xl">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-stone-50 border border-stone-200" />
              <span>No tasks</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-terracotta-100" />
              <span>&lt;33%</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-stone-100" />
              <span>33-67%</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-amber-100" />
              <span>67-99%</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-moss-100" />
              <span>100%</span>
            </div>
          </div>
        </main>
      </div>

      {/* Export Modal */}
      {showExportModal && (
        <ExportModal onClose={() => setShowExportModal(false)} />
      )}
    </div>
  )
}
```

**Step 2: Delete DayOverviewModal**

```bash
rm /Users/colindickson/code/telex/oliver/frontend/src/components/DayOverviewModal.tsx
```

**Step 3: Verify the TypeScript build compiles cleanly**

```bash
cd /Users/colindickson/code/telex/oliver/frontend && npx tsc --noEmit
```

Expected: No errors. If `ExportModal` complains that `initialDate` is now missing, check its props — if it was optional (has `?`), no change is needed. If it was required, remove the prop from the interface in `ExportModal.tsx`.

**Step 4: Commit**

```bash
cd /Users/colindickson/code/telex/oliver
git add frontend/src/pages/Calendar.tsx
git rm frontend/src/components/DayOverviewModal.tsx
git commit -m "Navigate all calendar days to DayDetail, remove DayOverviewModal"
```

---

### Task 3: DayDetail — completion toggle with future-date guard

**Files:**
- Modify: `frontend/src/pages/DayDetail.tsx`

The current DayDetail renders completion circles as static `<div>` elements. This task makes them interactive buttons, disabled for future dates.

**Step 1: Add imports and computed values**

At the top of `DayDetail.tsx`, update the imports to:

```tsx
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dayApi, taskApi } from '../api/client'
import type { Task } from '../api/client'
import { Sidebar } from '../components/Sidebar'
```

Inside the `DayDetail` function, after the existing `const navigate = useNavigate()` line, add:

```tsx
const qc = useQueryClient()
const todayStr = new Date().toISOString().slice(0, 10)
const isFuture = !!date && date > todayStr
```

**Step 2: Add the toggleStatus mutation**

After the `isFuture` line, add:

```tsx
const toggleStatus = useMutation({
  mutationFn: (task: Task) =>
    taskApi.setStatus(task.id, task.status === 'completed' ? 'pending' : 'completed'),
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ['day', date] })
    qc.invalidateQueries({ queryKey: ['days', 'all'] })
  },
})
```

**Step 3: Replace the static completion circle div with a button**

Find the existing completion circle in the task list (around line 134–145 of the original file). It currently reads:

```tsx
<div
  className={`w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center transition-colors ${
    task.status === 'completed'
      ? 'bg-moss-500'
      : 'bg-stone-200'
  }`}
>
  {task.status === 'completed' && (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="white" strokeWidth="2">
      <path d="M2 6L5 9L10 3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )}
</div>
```

Replace it with:

```tsx
<button
  onClick={() => !isFuture && toggleStatus.mutate(task)}
  disabled={isFuture}
  title={isFuture ? "Can't complete a future task" : undefined}
  className={`w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center transition-colors ${
    task.status === 'completed'
      ? 'bg-moss-500'
      : 'bg-stone-200'
  } ${isFuture ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer hover:opacity-80'}`}
>
  {task.status === 'completed' && (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="white" strokeWidth="2">
      <path d="M2 6L5 9L10 3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )}
</button>
```

**Step 4: Add "Planning" badge to the header for future dates**

Find the `<h1>` in the header that shows the formatted date. After it (still inside the `<div>` wrapping the back button and h1), add:

```tsx
{isFuture && (
  <span className="mt-1 inline-block text-xs font-medium text-ocean-600 bg-ocean-50 px-2 py-0.5 rounded-full">
    Planning
  </span>
)}
```

**Step 5: Verify the TypeScript build compiles cleanly**

```bash
cd /Users/colindickson/code/telex/oliver/frontend && npx tsc --noEmit
```

Expected: No errors.

**Step 6: Commit**

```bash
cd /Users/colindickson/code/telex/oliver
git add frontend/src/pages/DayDetail.tsx
git commit -m "Add completion toggle to DayDetail, guard future dates"
```

---

### Task 4: DayDetail — inline add-task form per category

**Files:**
- Modify: `frontend/src/pages/DayDetail.tsx`

**Step 1: Add state for the inline form**

Inside the `DayDetail` function, after the `toggleStatus` mutation, add:

```tsx
const [addingCategory, setAddingCategory] = useState<Task['category'] | null>(null)
const [newTaskTitle, setNewTaskTitle] = useState('')
```

Add `useState` to the React import at the top if it isn't already imported:
```tsx
import { useState } from 'react'
```

**Step 2: Add the createTask mutation**

After the `toggleStatus` mutation, add:

```tsx
const createTask = useMutation({
  mutationFn: (category: Task['category']) =>
    taskApi.create({ day_id: day!.id, category, title: newTaskTitle.trim() }),
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ['day', date] })
    qc.invalidateQueries({ queryKey: ['days', 'all'] })
    setNewTaskTitle('')
    setAddingCategory(null)
  },
})

function handleAddTask(category: Task['category']) {
  if (!newTaskTitle.trim() || !day) return
  createTask.mutate(category)
}
```

**Step 3: Add the "Add task" row and inline form to each category section**

Inside the `categories.map(cat => { ... })` block, after the closing `</div>` of the task list (the `space-y-2 rounded-2xl border ...` div), add the add-task UI before the outer closing `</div>`:

Find the end of the category section block. It currently ends like:

```tsx
                    </div>
                  </div>
                )
              })}
```

Before the final `</div>` that closes the category section, add:

```tsx
                    {/* Add task row */}
                    {addingCategory === cat.key ? (
                      <form
                        onSubmit={e => { e.preventDefault(); handleAddTask(cat.key) }}
                        className="flex items-center gap-2 mt-2"
                      >
                        <input
                          autoFocus
                          value={newTaskTitle}
                          onChange={e => setNewTaskTitle(e.target.value)}
                          onKeyDown={e => e.key === 'Escape' && (setAddingCategory(null), setNewTaskTitle(''))}
                          placeholder="Task title…"
                          className="flex-1 text-sm px-3 py-2 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-terracotta-300 bg-white"
                        />
                        <button
                          type="submit"
                          disabled={!newTaskTitle.trim()}
                          className="px-3 py-2 text-sm font-medium text-white bg-terracotta-500 rounded-xl hover:bg-terracotta-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                        >
                          Add
                        </button>
                        <button
                          type="button"
                          onClick={() => { setAddingCategory(null); setNewTaskTitle('') }}
                          className="px-3 py-2 text-sm text-stone-400 hover:text-stone-600 transition-colors"
                        >
                          Cancel
                        </button>
                      </form>
                    ) : (
                      <button
                        onClick={() => { setAddingCategory(cat.key); setNewTaskTitle('') }}
                        className={`mt-2 w-full text-left text-xs text-stone-400 hover:text-stone-600 flex items-center gap-1.5 px-1 py-1 rounded-lg hover:bg-white/60 transition-colors`}
                      >
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M6 2v8M2 6h8" strokeLinecap="round" />
                        </svg>
                        Add task
                      </button>
                    )}
```

**Step 4: Show categories even when they have no tasks (so "Add task" is always available)**

Currently the category map returns `null` when `tasks.length === 0`. Change this guard so all categories are always rendered:

Find:
```tsx
                if (tasks.length === 0) return null
```

Replace with:
```tsx
                if (tasks.length === 0 && addingCategory !== cat.key) {
                  // Render a minimal shell with just the add-task row
                  return (
                    <div key={cat.key}>
                      <div className="flex items-center justify-between mb-3">
                        <h2 className={`text-sm font-semibold uppercase tracking-wide ${cat.color}`}>
                          {cat.label}
                        </h2>
                      </div>
                      <div className={`rounded-2xl border ${cat.border} ${cat.bg} px-4 pt-2 pb-3`}>
                        {addingCategory === cat.key ? (
                          <form
                            onSubmit={e => { e.preventDefault(); handleAddTask(cat.key) }}
                            className="flex items-center gap-2"
                          >
                            <input
                              autoFocus
                              value={newTaskTitle}
                              onChange={e => setNewTaskTitle(e.target.value)}
                              onKeyDown={e => e.key === 'Escape' && (setAddingCategory(null), setNewTaskTitle(''))}
                              placeholder="Task title…"
                              className="flex-1 text-sm px-3 py-2 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-terracotta-300 bg-white"
                            />
                            <button
                              type="submit"
                              disabled={!newTaskTitle.trim()}
                              className="px-3 py-2 text-sm font-medium text-white bg-terracotta-500 rounded-xl hover:bg-terracotta-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                            >
                              Add
                            </button>
                            <button
                              type="button"
                              onClick={() => { setAddingCategory(null); setNewTaskTitle('') }}
                              className="px-3 py-2 text-sm text-stone-400 hover:text-stone-600 transition-colors"
                            >
                              Cancel
                            </button>
                          </form>
                        ) : (
                          <button
                            onClick={() => { setAddingCategory(cat.key); setNewTaskTitle('') }}
                            className="w-full text-left text-xs text-stone-400 hover:text-stone-600 flex items-center gap-1.5 px-1 py-1 rounded-lg hover:bg-white/60 transition-colors"
                          >
                            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M6 2v8M2 6h8" strokeLinecap="round" />
                            </svg>
                            Add task
                          </button>
                        )}
                      </div>
                    </div>
                  )
                }
```

Also update the `return null` case to just `return null` without the early guard — the empty-task case is now handled by the block above. Remove the original `if (tasks.length === 0) return null` line entirely (it's been replaced).

**Step 5: Replace the isError block with an empty-state message**

Since the backend now auto-creates days, a 404 should never occur. Replace the `isError` block:

Find:
```tsx
          {isError && (
            <div className="bg-terracotta-50 border border-terracotta-200 rounded-2xl p-6 text-center">
              <p className="text-terracotta-600">No data for this day.</p>
            </div>
          )}
```

Replace with:
```tsx
          {isError && (
            <div className="bg-terracotta-50 border border-terracotta-200 rounded-2xl p-6 text-center">
              <p className="text-terracotta-600">Could not load this day. Please try again.</p>
            </div>
          )}
```

Also remove the now-redundant "no tasks" empty state at the bottom of the `{day && ...}` block:

Find and delete:
```tsx
              {day.tasks.length === 0 && (
                <div className="text-center py-12 text-stone-400">
                  <p className="text-sm">No tasks recorded for this day.</p>
                </div>
              )}
```

**Step 6: Verify TypeScript compiles cleanly**

```bash
cd /Users/colindickson/code/telex/oliver/frontend && npx tsc --noEmit
```

Expected: No errors.

**Step 7: Commit**

```bash
cd /Users/colindickson/code/telex/oliver
git add frontend/src/pages/DayDetail.tsx
git commit -m "Add inline task creation to DayDetail"
```

---

### Task 5: Manual smoke test and PR

**Step 1: Start the app**

```bash
# Terminal 1 — backend
cd /Users/colindickson/code/telex/oliver/backend && uvicorn app.main:app --reload

# Terminal 2 — frontend
cd /Users/colindickson/code/telex/oliver/frontend && npm run dev
```

**Step 2: Verify these scenarios**

- [ ] Click an existing day on the calendar → goes to DayDetail, shows existing tasks
- [ ] Click an empty past day → goes to DayDetail, shows three categories with "Add task" rows, no "Planning" badge
- [ ] Click a future day → goes to DayDetail with "Planning" badge, completion circles are dimmed, "Add task" rows present
- [ ] Add a task on a past day → task appears in the list
- [ ] Add a task on a future day → task appears in the list
- [ ] Toggle completion on a past/today task → circle turns green, task gets strikethrough
- [ ] Try clicking a completion circle on a future day → nothing happens, cursor is not-allowed
- [ ] Navigate back to Calendar → previously-empty day now shows task count
- [ ] DayOverviewModal no longer appears anywhere

**Step 3: Open PR**

```bash
cd /Users/colindickson/code/telex/oliver
git push -u origin feature/day-navigation
gh pr create --title "Add day navigation and editing" --body "$(cat <<'EOF'
## Summary
- All calendar cells now navigate to DayDetail for any date
- Backend auto-creates Day records on GET instead of returning 404
- DayDetail gains inline task creation (per category) and completion toggling
- Future dates show a Planning badge; completion is disabled with a tooltip
- DayOverviewModal removed

## Test plan
- [ ] Click every type of calendar cell (past with data, past empty, today, future)
- [ ] Add tasks on past and future days
- [ ] Toggle task completion on past/today tasks
- [ ] Verify completion circles are inert on future days
- [ ] Verify Calendar reflects task counts for newly-planned days

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```
