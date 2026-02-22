// frontend/src/components/DayOverviewModal.tsx
import { useState, useEffect } from 'react'
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

  // Escape key handler
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

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
        role="dialog"
        aria-modal="true"
        aria-labelledby="day-overview-title"
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
            <h2 id="day-overview-title" className="text-base font-semibold text-stone-800">{formattedDate}</h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
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
          aria-expanded={expanded}
          aria-label={expanded ? 'Hide tasks' : 'Show all tasks'}
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
              <path d="M3 8h10M9 4l4 4 4 4" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
