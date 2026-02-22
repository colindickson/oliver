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
