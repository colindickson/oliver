# Task Inline Editing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add inline editing for task title, description, and tags on the DayDetail page.

**Architecture:** Extract the inline editing logic from TaskCard into a reusable `useTaskEdit` hook, then apply it to both TaskCard and DayDetail task items.

**Tech Stack:** React, TypeScript, TanStack Query, axios

---

### Task 1: Create useTaskEdit Hook

**Files:**
- Create: `frontend/src/hooks/useTaskEdit.ts`

**Step 1: Create the hook file**

```typescript
import { useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { Task } from '../api/client'
import { taskApi } from '../api/client'

interface UseTaskEditOptions {
  task: Task
  onSuccess?: () => void
}

interface UseTaskEditReturn {
  editing: boolean
  editTitle: string
  editDescription: string
  editTags: string[]
  saving: boolean
  openEdit: () => void
  saveEdit: () => Promise<void>
  cancelEdit: () => void
  setEditTitle: (title: string) => void
  setEditDescription: (description: string) => void
  setEditTags: (tags: string[]) => void
}

export function useTaskEdit({ task, onSuccess }: UseTaskEditOptions): UseTaskEditReturn {
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(task.title)
  const [editDescription, setEditDescription] = useState(task.description ?? '')
  const [editTags, setEditTags] = useState<string[]>(task.tags ?? [])
  const [saving, setSaving] = useState(false)

  const openEdit = useCallback(() => {
    setEditTitle(task.title)
    setEditDescription(task.description ?? '')
    setEditTags(task.tags ?? [])
    setEditing(true)
  }, [task.title, task.description, task.tags])

  const saveEdit = useCallback(async () => {
    if (!editTitle.trim()) return
    setSaving(true)
    try {
      await taskApi.update(task.id, {
        title: editTitle.trim(),
        description: editDescription.trim() || null,
        tags: editTags,
      })
      qc.invalidateQueries({ queryKey: ['day'] })
      qc.invalidateQueries({ queryKey: ['tags'] })
      setEditing(false)
      onSuccess?.()
    } finally {
      setSaving(false)
    }
  }, [task.id, editTitle, editDescription, editTags, qc, onSuccess])

  const cancelEdit = useCallback(() => {
    setEditing(false)
  }, [])

  return {
    editing,
    editTitle,
    editDescription,
    editTags,
    saving,
    openEdit,
    saveEdit,
    cancelEdit,
    setEditTitle,
    setEditDescription,
    setEditTags,
  }
}
```

**Step 2: Commit**

```bash
git add frontend/src/hooks/useTaskEdit.ts
git commit -m "feat: add useTaskEdit hook for reusable task editing"
```

---

### Task 2: Refactor TaskCard to use useTaskEdit Hook

**Files:**
- Modify: `frontend/src/components/TaskCard.tsx`

**Step 1: Update imports and replace local state with hook**

Replace the existing editing state and handlers with the hook. Key changes:

1. Add import for `useTaskEdit`
2. Replace useState calls for editing, editTitle, editDescription, editTags, saving
3. Replace handleEditOpen with openEdit from hook
4. Replace handleSave with saveEdit from hook
5. Use setEditTitle, setEditDescription, setEditTags from hook

The component props stay the same. The JSX stays mostly the same, just using the hook's values.

```typescript
import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { Task } from '../api/client'
import { ReminderDialog } from './ReminderDialog'
import { TagInput } from './TagInput'
import { useTaskEdit } from '../hooks/useTaskEdit'

interface Props {
  task: Task
  onComplete: (task: Task) => void
  onDelete: (id: number) => void
}

export function TaskCard({ task, onComplete, onDelete }: Props) {
  const isCompleted = task.status === 'completed'
  const [showReminder, setShowReminder] = useState(false)

  const {
    editing,
    editTitle,
    editDescription,
    editTags,
    saving,
    openEdit,
    saveEdit,
    cancelEdit,
    setEditTitle,
    setEditDescription,
    setEditTags,
  } = useTaskEdit({ task })

  // ... rest of component unchanged, just use hook values
```

**Step 2: Update event handlers to use hook**

In the editing JSX, update:
- `onKeyDown` for Enter to call `void saveEdit()` instead of `void handleSave()`
- `onKeyDown` for Escape to call `cancelEdit()` instead of `setEditing(false)`
- Save button onClick to call `void saveEdit()`
- Cancel button onClick to call `cancelEdit()`
- Edit button onClick to call `openEdit` instead of `handleEditOpen`

**Step 3: Manual test**

1. Start frontend: `make dev-frontend`
2. Navigate to Today page
3. Verify edit button appears on hover
4. Click edit, verify form opens with current values
5. Edit title/description/tags, save - verify updates persist
6. Test cancel - verify changes discarded
7. Test keyboard: Enter saves, Escape cancels

**Step 4: Commit**

```bash
git add frontend/src/components/TaskCard.tsx
git commit -m "refactor: TaskCard uses useTaskEdit hook"
```

---

### Task 3: Add Inline Editing to DayDetail

**Files:**
- Modify: `frontend/src/pages/DayDetail.tsx`

**Step 1: Add import for useTaskEdit and TagInput**

Add to imports:
```typescript
import { useTaskEdit } from '../hooks/useTaskEdit'
```

(Note: TagInput is already imported)

**Step 2: Create TaskItem component inside DayDetail**

Create a new component at the top of the file (after imports, before `AddTaskForm`) that handles the inline editing for each task:

```typescript
interface TaskItemProps {
  task: Task
  isFuture: boolean
  onToggleStatus: (task: Task) => void
  onDelete: (id: number) => void
}

function TaskItem({ task, isFuture, onToggleStatus, onDelete }: TaskItemProps) {
  const {
    editing,
    editTitle,
    editDescription,
    editTags,
    saving,
    openEdit,
    saveEdit,
    cancelEdit,
    setEditTitle,
    setEditDescription,
    setEditTags,
  } = useTaskEdit({ task })

  const isCompleted = task.status === 'completed'

  if (editing) {
    return (
      <div className="bg-white rounded-xl border border-terracotta-200 p-4 space-y-2 dark:bg-stone-800 dark:border-terracotta-700/40">
        <input
          autoFocus
          type="text"
          value={editTitle}
          onChange={e => setEditTitle(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') void saveEdit()
            if (e.key === 'Escape') cancelEdit()
          }}
          className="w-full text-sm border border-stone-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent dark:bg-stone-700 dark:border-stone-600 dark:text-stone-100"
        />
        <textarea
          value={editDescription}
          onChange={e => setEditDescription(e.target.value)}
          placeholder="Description (optional)"
          rows={2}
          className="w-full text-sm border border-stone-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent resize-none dark:bg-stone-700 dark:border-stone-600 dark:text-stone-100 dark:placeholder-stone-400"
        />
        <TagInput value={editTags} onChange={setEditTags} />
        <div className="flex gap-2 pt-0.5">
          <button
            type="button"
            onClick={() => void saveEdit()}
            disabled={saving || !editTitle.trim()}
            className="text-xs bg-stone-800 text-white rounded-lg px-3 py-1.5 hover:bg-stone-700 disabled:opacity-50 transition-all dark:bg-stone-600 dark:hover:bg-stone-500"
          >
            Save
          </button>
          <button
            type="button"
            onClick={cancelEdit}
            className="text-xs text-stone-400 hover:text-stone-600 transition-colors px-2 dark:text-stone-500 dark:hover:text-stone-300"
          >
            Cancel
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="group bg-white rounded-xl border border-stone-100 p-4 flex items-start gap-3 shadow-sm dark:bg-stone-800 dark:border-stone-700/50">
      <button
        onClick={() => !isFuture && onToggleStatus(task)}
        disabled={isFuture}
        title={isFuture ? "Can't complete a future task" : undefined}
        className={`mt-0.5 w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center transition-colors ${
          isCompleted
            ? 'bg-moss-500'
            : 'bg-stone-200 dark:bg-stone-600'
        } ${isFuture ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer hover:opacity-80'}`}
      >
        {isCompleted && (
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="white" strokeWidth="2">
            <path d="M2 6L5 9L10 3" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
      </button>
      <div className="flex-1 min-w-0">
        <span
          className={`text-sm transition-colors ${
            isCompleted
              ? 'line-through text-stone-400'
              : 'text-stone-800 dark:text-stone-100'
          }`}
        >
          {task.title}
        </span>
        {task.description && (
          <span className="text-xs text-stone-400 truncate block">
            {task.description}
          </span>
        )}
        {task.tags && task.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {task.tags.map(tag => (
              <span
                key={tag}
                className="text-xs px-1.5 py-0.5 rounded-full bg-stone-100 text-stone-500 dark:bg-stone-700 dark:text-stone-400"
              >
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="flex items-center gap-1 flex-shrink-0">
        <button
          onClick={openEdit}
          className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-stone-500 hover:bg-stone-50 rounded transition-colors opacity-0 group-hover:opacity-100 dark:text-stone-600 dark:hover:text-stone-300 dark:hover:bg-stone-700"
          aria-label="Edit task"
        >
          <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M9 2L11 4L5 10H3V8L9 2Z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <button
          onClick={() => onDelete(task.id)}
          className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-red-400 hover:bg-red-50 rounded transition-colors opacity-0 group-hover:opacity-100 dark:text-stone-600 dark:hover:text-red-400 dark:hover:bg-stone-700"
          title="Delete task"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M3.5 4L4.5 12H9.5L10.5 4" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M2 4H12" strokeLinecap="round" />
            <path d="M5 4V2.5H9V4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>
    </div>
  )
}
```

**Step 3: Replace inline task JSX with TaskItem component**

In the `categories.map` loop, replace the task div (lines 305-362) with:

```typescript
{tasks.map(task => (
  <TaskItem
    key={task.id}
    task={task}
    isFuture={isFuture}
    onToggleStatus={(task) => toggleStatus.mutate(task)}
    onDelete={(id) => deleteTask.mutate(id)}
  />
))}
```

**Step 4: Manual test**

1. Start dev environment: `make dev`
2. Navigate to a day detail page (e.g., `/day/2026-02-24`)
3. Verify edit button appears on task hover
4. Click edit, verify form opens with current values
5. Edit title/description/tags, save - verify updates persist
6. Test cancel - verify changes discarded
7. Test on past day, future day, today
8. Verify completion toggle still works
9. Verify delete still works

**Step 5: Commit**

```bash
git add frontend/src/pages/DayDetail.tsx
git commit -m "feat: add inline editing to DayDetail tasks"
```

---

### Task 4: Final Verification

**Step 1: Run full stack and verify**

```bash
make dev
```

**Step 2: Test all scenarios**

- [ ] Today page task editing still works
- [ ] DayDetail past task editing works
- [ ] DayDetail today task editing works
- [ ] DayDetail future task editing works
- [ ] Edit form shows current values correctly
- [ ] Save persists changes
- [ ] Cancel discards changes
- [ ] Enter key saves
- [ ] Escape key cancels
- [ ] Tags update correctly
- [ ] Query invalidation refreshes UI

**Step 3: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: any issues found during verification"
```
