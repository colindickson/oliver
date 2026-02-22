# Day Overview Modal and JSON Export Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a modal showing day overview on calendar click, plus JSON export for day/week/custom ranges.

**Architecture:** Two new modal components (DayOverviewModal, ExportModal) following existing ReminderDialog pattern. Export uses client-side data filtering and browser Blob download. Calendar modified to open modal on click instead of navigating.

**Tech Stack:** React 18, TypeScript, Tailwind CSS, TanStack Query, existing API client

---

## Task 1: Create Export Utility Functions

**Files:**
- Create: `frontend/src/utils/export.ts`

**Step 1: Create the export utility file**

Create pure utility functions for building the export JSON and triggering browser download.

```typescript
// frontend/src/utils/export.ts
import type { DayResponse, Task, TimerSession } from '../api/client'

interface ExportMetadata {
  exported_at: string
  period: {
    type: 'day' | 'week' | 'custom_range'
    from: string
    to: string
  }
}

interface CategoryStats {
  total: number
  completed: number
}

interface ExportSummary {
  total_tasks: number
  completed: number
  completion_rate: number
  by_category: {
    deep_work: CategoryStats
    short_task: CategoryStats
    maintenance: CategoryStats
  }
}

interface TaskExport {
  id: number
  title: string
  description: string | null
  category: Task['category']
  status: Task['status']
  completed_at: string | null
  order_index: number
  timer_sessions: Array<{
    started_at: string
    duration_seconds: number
  }>
}

interface DayExport {
  date: string
  day_id: number
  total_tasks: number
  completed: number
  completion_rate: number
  tasks: TaskExport[]
}

export interface ExportData {
  export_metadata: ExportMetadata
  summary: ExportSummary
  days: DayExport[]
}

export function buildExportData(
  days: DayResponse[],
  periodType: 'day' | 'week' | 'custom_range',
  from: string,
  to: string,
  timerSessionsByTask: Map<number, TimerSession[]>
): ExportData {
  const filteredDays = days.filter(d => d.date >= from && d.date <= to)

  const allTasks = filteredDays.flatMap(d => d.tasks)
  const totalTasks = allTasks.length
  const completedTasks = allTasks.filter(t => t.status === 'completed').length

  const byCategory = {
    deep_work: buildCategoryStats(allTasks, 'deep_work'),
    short_task: buildCategoryStats(allTasks, 'short_task'),
    maintenance: buildCategoryStats(allTasks, 'maintenance'),
  }

  const dayExports: DayExport[] = filteredDays.map(day => ({
    date: day.date,
    day_id: day.id,
    total_tasks: day.tasks.length,
    completed: day.tasks.filter(t => t.status === 'completed').length,
    completion_rate: day.tasks.length > 0
      ? day.tasks.filter(t => t.status === 'completed').length / day.tasks.length
      : 0,
    tasks: day.tasks.map(task => ({
      id: task.id,
      title: task.title,
      description: task.description,
      category: task.category,
      status: task.status,
      completed_at: task.completed_at,
      order_index: task.order_index,
      timer_sessions: (timerSessionsByTask.get(task.id) ?? []).map(s => ({
        started_at: s.started_at,
        duration_seconds: s.duration_seconds ?? 0,
      })),
    })),
  }))

  return {
    export_metadata: {
      exported_at: new Date().toISOString(),
      period: { type: periodType, from, to },
    },
    summary: {
      total_tasks: totalTasks,
      completed: completedTasks,
      completion_rate: totalTasks > 0 ? completedTasks / totalTasks : 0,
      by_category: byCategory,
    },
    days: dayExports,
  }
}

function buildCategoryStats(tasks: Task[], category: Task['category']): CategoryStats {
  const categoryTasks = tasks.filter(t => t.category === category)
  return {
    total: categoryTasks.length,
    completed: categoryTasks.filter(t => t.status === 'completed').length,
  }
}

export function downloadJson(data: ExportData, filename: string): void {
  const json = JSON.stringify(data, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export function generateExportFilename(from: string, to: string): string {
  if (from === to) {
    return `tasks-export-${from}.json`
  }
  return `tasks-export-${from}-to-${to}.json`
}

export function getWeekBounds(date: Date): { start: string; end: string } {
  const d = new Date(date)
  const day = d.getDay()
  const diffToMonday = day === 0 ? -6 : 1 - day

  const monday = new Date(d)
  monday.setDate(d.getDate() + diffToMonday)

  const sunday = new Date(monday)
  sunday.setDate(monday.getDate() + 6)

  return {
    start: monday.toISOString().slice(0, 10),
    end: sunday.toISOString().slice(0, 10),
  }
}
```

**Step 2: Verify the file compiles**

Run: `cd frontend && npm run build`
Expected: Build succeeds without errors

**Step 3: Commit**

```bash
git add frontend/src/utils/export.ts
git commit -m "Add export utility functions for JSON export"
```

---

## Task 2: Create DayOverviewModal Component

**Files:**
- Create: `frontend/src/components/DayOverviewModal.tsx`

**Step 1: Create the DayOverviewModal component**

```typescript
// frontend/src/components/DayOverviewModal.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { DayResponse, Task } from '../api/client'

interface Props {
  day: DayResponse
  onClose: () => void
  onExport: () => void
}

const categoryConfig = {
  deep_work: { label: 'Deep Work', color: 'ocean' },
  short_task: { label: 'Short Tasks', color: 'terracotta' },
  maintenance: { label: 'Maintenance', color: 'moss' },
} as const

function getCategoryStats(tasks: Task[]) {
  const total = tasks.length
  const completed = tasks.filter(t => t.status === 'completed').length
  return { total, completed }
}

function groupByCategory(tasks: Task[]): Record<Task['category'], Task[]> {
  return {
    deep_work: tasks.filter(t => t.category === 'deep_work'),
    short_task: tasks.filter(t => t.category === 'short_task'),
    maintenance: tasks.filter(t => t.category === 'maintenance'),
  }
}

export function DayOverviewModal({ day, onClose, onExport }: Props) {
  const navigate = useNavigate()
  const [expanded, setExpanded] = useState(false)

  const stats = getCategoryStats(day.tasks)
  const completionRate = stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0
  const grouped = groupByCategory(day.tasks)

  const formattedDate = new Date(day.date + 'T00:00:00').toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })

  function handleBackdropClick() {
    onClose()
  }

  function handleDialogClick(e: React.MouseEvent) {
    e.stopPropagation()
  }

  function handleViewFullPage() {
    navigate(`/day/${day.date}`)
    onClose()
  }

  return (
    <div
      className="fixed inset-0 bg-stone-900/50 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in"
      onClick={handleBackdropClick}
    >
      <div
        className="bg-white rounded-2xl shadow-soft-lg p-6 w-full max-w-md mx-4 animate-slide-up"
        onClick={handleDialogClick}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-terracotta-100 flex items-center justify-center">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="#c2410c" strokeWidth="1.5">
                <rect x="3" y="4" width="14" height="13" rx="2" />
                <path d="M3 8h14" />
                <path d="M7 2v3" />
                <path d="M13 2v3" />
              </svg>
            </div>
            <h2 className="text-base font-semibold text-stone-800">{formattedDate}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-stone-400 hover:text-stone-600 transition-colors"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M5 5l10 10M15 5L5 15" />
            </svg>
          </button>
        </div>

        {/* Summary Card */}
        <div className="bg-stone-50 rounded-xl p-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-stone-600">
              {stats.total} tasks total
            </span>
            <span className="text-sm font-semibold text-stone-800">
              {stats.completed} completed ({completionRate}%)
            </span>
          </div>
          <div className="space-y-2">
            {(['deep_work', 'short_task', 'maintenance'] as const).map(cat => {
              const catStats = getCategoryStats(grouped[cat])
              if (catStats.total === 0) return null
              const config = categoryConfig[cat]
              return (
                <div key={cat} className="flex items-center justify-between text-sm">
                  <span className="text-stone-500">{config.label}</span>
                  <span className="text-stone-700">
                    {catStats.completed}/{catStats.total} tasks
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Expand/Collapse Toggle */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-center gap-2 py-2 text-sm font-medium text-stone-500 hover:text-stone-700 transition-colors mb-4"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className={`transition-transform ${expanded ? 'rotate-180' : ''}`}
          >
            <path d="M4 6l4 4 4-4" />
          </svg>
          {expanded ? 'Hide tasks' : 'Show all tasks'}
        </button>

        {/* Expanded Task List */}
        {expanded && (
          <div className="max-h-64 overflow-y-auto space-y-4 mb-4">
            {(['deep_work', 'short_task', 'maintenance'] as const).map(cat => {
              const tasks = grouped[cat]
              if (tasks.length === 0) return null
              const config = categoryConfig[cat]
              const catStats = getCategoryStats(tasks)
              return (
                <div key={cat}>
                  <h3 className="text-xs font-medium text-stone-400 uppercase tracking-wider mb-2">
                    {config.label} ({catStats.completed}/{catStats.total})
                  </h3>
                  <ul className="space-y-1">
                    {tasks.map(task => (
                      <li
                        key={task.id}
                        className="flex items-center gap-2 text-sm py-1"
                      >
                        {task.status === 'completed' ? (
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-moss-500 flex-shrink-0">
                            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
                            <path d="M5 8l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        ) : (
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-stone-300 flex-shrink-0">
                            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
                          </svg>
                        )}
                        <span className={task.status === 'completed' ? 'text-stone-400 line-through' : 'text-stone-700'}>
                          {task.title}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )
            })}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onExport}
            className="flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-stone-600 bg-stone-100 rounded-xl hover:bg-stone-200 transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M8 2v8M5 7l3 3 3-3" />
              <path d="M2 12v1a1 1 0 001 1h10a1 1 0 001-1v-1" />
            </svg>
            Export
          </button>
          <button
            onClick={handleViewFullPage}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium text-terracotta-600 hover:text-terracotta-700 transition-colors"
          >
            View full page
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M3 8h10M9 4l4 4-4 4" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Verify the file compiles**

Run: `cd frontend && npm run build`
Expected: Build succeeds without errors

**Step 3: Commit**

```bash
git add frontend/src/components/DayOverviewModal.tsx
git commit -m "Add DayOverviewModal component"
```

---

## Task 3: Create ExportModal Component

**Files:**
- Create: `frontend/src/components/ExportModal.tsx`

**Step 1: Create the ExportModal component**

```typescript
// frontend/src/components/ExportModal.tsx
import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { dayApi, timerApi } from '../api/client'
import type { DayResponse, TimerSession } from '../api/client'
import { buildExportData, downloadJson, generateExportFilename, getWeekBounds, type ExportData } from '../utils/export'

interface Props {
  onClose: () => void
  initialDate?: string
}

type PeriodType = 'day' | 'week' | 'custom'

export function ExportModal({ onClose, initialDate }: Props) {
  const [periodType, setPeriodType] = useState<PeriodType>('day')
  const [customFrom, setCustomFrom] = useState(initialDate ?? new Date().toISOString().slice(0, 10))
  const [customTo, setCustomTo] = useState(initialDate ?? new Date().toISOString().slice(0, 10))
  const [exporting, setExporting] = useState(false)

  const { data: days = [] } = useQuery({
    queryKey: ['days', 'all'],
    queryFn: dayApi.getAll,
  })

  // Calculate date range based on period type
  const dateRange = getDateRange(periodType, initialDate, customFrom, customTo)

  // Get preview stats
  const previewDays = days.filter(d => d.date >= dateRange.from && d.date <= dateRange.to)
  const previewStats = {
    dayCount: previewDays.length,
    taskCount: previewDays.flatMap(d => d.tasks).length,
    completedCount: previewDays.flatMap(d => d.tasks).filter(t => t.status === 'completed').length,
  }

  function getDateRange(type: PeriodType, initial?: string, from?: string, to?: string) {
    const baseDate = initial ? new Date(initial + 'T00:00:00') : new Date()

    switch (type) {
      case 'day':
        const dayStr = initial ?? new Date().toISOString().slice(0, 10)
        return { from: dayStr, to: dayStr }
      case 'week':
        return getWeekBounds(baseDate)
      case 'custom':
        return { from: from ?? '', to: to ?? '' }
    }
  }

  async function handleExport() {
    if (!dateRange.from || !dateRange.to) return

    setExporting(true)
    try {
      // Fetch timer sessions for all tasks in the range
      const tasksInRange = previewDays.flatMap(d => d.tasks)
      const sessionsByTask = new Map<number, TimerSession[]>()

      await Promise.all(
        tasksInRange.map(async task => {
          try {
            const sessions = await timerApi.getSessions(task.id)
            sessionsByTask.set(task.id, sessions)
          } catch {
            sessionsByTask.set(task.id, [])
          }
        })
      )

      const exportData = buildExportData(
        days,
        periodType === 'custom' ? 'custom_range' : periodType,
        dateRange.from,
        dateRange.to,
        sessionsByTask
      )

      const filename = generateExportFilename(dateRange.from, dateRange.to)
      downloadJson(exportData, filename)
      onClose()
    } finally {
      setExporting(false)
    }
  }

  function handleBackdropClick() {
    onClose()
  }

  function handleDialogClick(e: React.MouseEvent) {
    e.stopPropagation()
  }

  const formattedRange = dateRange.from === dateRange.to
    ? new Date(dateRange.from + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    : `${new Date(dateRange.from + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${new Date(dateRange.to + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`

  return (
    <div
      className="fixed inset-0 bg-stone-900/50 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in"
      onClick={handleBackdropClick}
    >
      <div
        className="bg-white rounded-2xl shadow-soft-lg p-6 w-full max-w-sm mx-4 animate-slide-up"
        onClick={handleDialogClick}
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-ocean-100 flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="#0369a1" strokeWidth="1.5">
              <path d="M10 2v10M6 8l4 4 4-4" />
              <path d="M3 14v2a1 1 0 001 1h12a1 1 0 001-1v-2" />
            </svg>
          </div>
          <h2 className="text-base font-semibold text-stone-800">Export Tasks</h2>
        </div>

        {/* Period Selection */}
        <div className="mb-5">
          <label className="text-xs font-medium text-stone-500 uppercase tracking-wider block mb-2">
            Export Period
          </label>
          <div className="flex gap-2">
            {(['day', 'week', 'custom'] as const).map(type => (
              <button
                key={type}
                onClick={() => setPeriodType(type)}
                className={`flex-1 py-2 text-sm font-medium rounded-xl transition-colors ${
                  periodType === type
                    ? 'bg-ocean-100 text-ocean-700'
                    : 'bg-stone-100 text-stone-500 hover:bg-stone-200'
                }`}
              >
                {type === 'day' ? 'Day' : type === 'week' ? 'Week' : 'Custom'}
              </button>
            ))}
          </div>
        </div>

        {/* Custom Date Range */}
        {periodType === 'custom' && (
          <div className="mb-5 space-y-3">
            <div>
              <label className="text-xs font-medium text-stone-500 uppercase tracking-wider block mb-2">
                From
              </label>
              <input
                type="date"
                value={customFrom}
                onChange={e => setCustomFrom(e.target.value)}
                className="w-full text-sm border border-stone-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-ocean-300 focus:border-transparent transition-shadow"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-stone-500 uppercase tracking-wider block mb-2">
                To
              </label>
              <input
                type="date"
                value={customTo}
                onChange={e => setCustomTo(e.target.value)}
                className="w-full text-sm border border-stone-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-ocean-300 focus:border-transparent transition-shadow"
              />
            </div>
          </div>
        )}

        {/* Preview */}
        <div className="bg-stone-50 rounded-xl p-4 mb-5">
          <div className="text-sm text-stone-600 mb-1">{formattedRange}</div>
          <div className="text-sm text-stone-500">
            {previewStats.dayCount} {previewStats.dayCount === 1 ? 'day' : 'days'} • {previewStats.taskCount} tasks • {previewStats.taskCount > 0 ? Math.round((previewStats.completedCount / previewStats.taskCount) * 100) : 0}% complete
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="px-5 text-sm text-stone-500 hover:text-stone-700 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => void handleExport()}
            disabled={exporting || !dateRange.from || !dateRange.to || previewStats.taskCount === 0}
            className="flex-1 bg-ocean-600 text-white text-sm font-medium rounded-xl py-2.5 hover:bg-ocean-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {exporting ? (
              <>
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Exporting...
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M8 2v8M5 7l3 3 3-3" />
                  <path d="M2 12v1a1 1 0 001 1h10a1 1 0 001-1v-1" />
                </svg>
                Download JSON
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Verify the file compiles**

Run: `cd frontend && npm run build`
Expected: Build succeeds without errors

**Step 3: Commit**

```bash
git add frontend/src/components/ExportModal.tsx
git commit -m "Add ExportModal component"
```

---

## Task 4: Update Calendar to Use Modals

**Files:**
- Modify: `frontend/src/pages/Calendar.tsx`

**Step 1: Update Calendar.tsx to integrate modals**

Add modal state and wire up DayOverviewModal and ExportModal.

```typescript
// frontend/src/pages/Calendar.tsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { dayApi } from '../api/client'
import type { DayResponse, Task } from '../api/client'
import { Sidebar } from '../components/Sidebar'
import { DayOverviewModal } from '../components/DayOverviewModal'
import { ExportModal } from '../components/ExportModal'

function getCompletionRate(tasks: Task[]): number {
  if (tasks.length === 0) return 0
  const completed = tasks.filter(t => t.status === 'completed').length
  return completed / tasks.length
}

export function Calendar() {
  const [viewDate, setViewDate] = useState(new Date())
  const [selectedDay, setSelectedDay] = useState<DayResponse | null>(null)
  const [showExportModal, setShowExportModal] = useState(false)

  const { data: days = [] } = useQuery({
    queryKey: ['days', 'all'],
    queryFn: dayApi.getAll,
  })

  const dayMap = new Map<string, DayResponse>(days.map(d => [d.date, d]))

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

  function handleDayClick(dateStr: string) {
    const dayData = dayMap.get(dateStr)
    if (dayData) {
      setSelectedDay(dayData)
    }
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

              let bgClass = 'bg-stone-50 text-stone-300'
              if (hasTasks) {
                if (rate >= 1) bgClass = 'bg-moss-100 text-moss-700 hover:bg-moss-200'
                else if (rate >= 0.67) bgClass = 'bg-amber-50 text-amber-700 hover:bg-amber-100'
                else if (rate >= 0.33) bgClass = 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                else bgClass = 'bg-terracotta-50 text-terracotta-700 hover:bg-terracotta-100'
              }

              return (
                <button
                  key={dateStr}
                  onClick={() => handleDayClick(dateStr)}
                  disabled={!hasTasks}
                  className={`
                    aspect-square flex flex-col items-center justify-center rounded-xl text-sm font-medium
                    transition-all duration-200
                    ${bgClass}
                    ${isToday ? 'ring-2 ring-terracotta-500 ring-offset-2' : ''}
                    ${hasTasks ? 'cursor-pointer hover:shadow-soft hover:-translate-y-0.5' : 'cursor-default'}
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

      {/* Day Overview Modal */}
      {selectedDay && (
        <DayOverviewModal
          day={selectedDay}
          onClose={() => setSelectedDay(null)}
          onExport={() => {
            setSelectedDay(null)
            setShowExportModal(true)
          }}
        />
      )}

      {/* Export Modal */}
      {showExportModal && (
        <ExportModal
          onClose={() => setShowExportModal(false)}
          initialDate={selectedDay?.date}
        />
      )}
    </div>
  )
}
```

**Step 2: Verify the build**

Run: `cd frontend && npm run build`
Expected: Build succeeds without errors

**Step 3: Manual verification**

1. Start the dev server: `cd frontend && npm run dev`
2. Navigate to `/calendar`
3. Click on a day with tasks → DayOverviewModal should open
4. Click Export button in modal → ExportModal should open with that date
5. Click Export in header → ExportModal should open
6. Test Day/Week/Custom period selection
7. Test JSON download

**Step 4: Commit**

```bash
git add frontend/src/pages/Calendar.tsx
git commit -m "Integrate DayOverviewModal and ExportModal into Calendar"
```

---

## Task 5: Final Integration Test and Polish

**Step 1: Run full build and type check**

Run: `cd frontend && npm run build`
Expected: Clean build with no warnings

**Step 2: Test all user flows**

1. **Day click → Modal opens**
   - Click on a day with tasks
   - Verify modal shows correct date and task counts
   - Verify expand/collapse works
   - Verify "View full page" navigates to /day/{date}

2. **Export from modal**
   - Open day modal
   - Click Export button
   - Verify ExportModal opens with that date pre-selected

3. **Export from header**
   - Click Export in calendar header
   - Verify ExportModal opens with today's date

4. **Export period selection**
   - Test Day mode: exports single day
   - Test Week mode: calculates Mon-Sun
   - Test Custom mode: date pickers work

5. **JSON download**
   - Export a period with tasks
   - Verify JSON file downloads
   - Verify JSON structure matches design

**Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "Polish day overview modal and export feature"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Export utility functions | `frontend/src/utils/export.ts` |
| 2 | DayOverviewModal component | `frontend/src/components/DayOverviewModal.tsx` |
| 3 | ExportModal component | `frontend/src/components/ExportModal.tsx` |
| 4 | Integrate into Calendar | `frontend/src/pages/Calendar.tsx` |
| 5 | Final testing | - |
