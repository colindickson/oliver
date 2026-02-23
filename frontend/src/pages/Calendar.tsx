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

  const todayStr = new Date().toLocaleDateString('en-CA')

  const monthLabel = viewDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

  function prevMonth() {
    setViewDate(new Date(year, month - 1, 1))
  }
  function nextMonth() {
    setViewDate(new Date(year, month + 1, 1))
  }

  return (
    <div className="flex min-h-screen bg-stone-25 dark:bg-stone-800">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-stone-200 px-8 py-5 flex items-center justify-between flex-shrink-0 dark:bg-stone-800/90 dark:border-stone-700/50">
          <h1 className="text-xl font-semibold text-stone-800 dark:text-stone-100">Calendar</h1>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowExportModal(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-stone-600 bg-white border border-stone-200 rounded-xl hover:bg-stone-50 hover:border-stone-300 transition-all dark:text-stone-300 dark:bg-stone-700 dark:border-stone-600 dark:hover:bg-stone-600"
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
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-stone-600 bg-white border border-stone-200 rounded-xl hover:bg-stone-50 hover:border-stone-300 transition-all dark:text-stone-300 dark:bg-stone-700 dark:border-stone-600 dark:hover:bg-stone-600"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10 4L6 8L10 12" />
              </svg>
              Previous
            </button>

            <button
              onClick={() => setViewDate(new Date())}
              className="px-4 py-2 text-sm font-medium text-terracotta-600 bg-terracotta-50 rounded-xl hover:bg-terracotta-100 transition-colors dark:text-terracotta-300 dark:bg-terracotta-900/20 dark:hover:bg-terracotta-900/30"
            >
              Today
            </button>

            <button
              onClick={nextMonth}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-stone-600 bg-white border border-stone-200 rounded-xl hover:bg-stone-50 hover:border-stone-300 transition-all dark:text-stone-300 dark:bg-stone-700 dark:border-stone-600 dark:hover:bg-stone-600"
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

              const dateStr = cellDate.toLocaleDateString('en-CA')
              const dayData = dayMap.get(dateStr)
              const tasks = dayData?.tasks ?? []
              const isToday = dateStr === todayStr
              const hasTasks = tasks.length > 0
              const completed = tasks.filter(t => t.status === 'completed').length
              const rate = getCompletionRate(tasks)

              let bgClass = 'bg-stone-50 text-stone-400 hover:bg-stone-100 dark:bg-stone-700/40 dark:text-stone-500 dark:hover:bg-stone-700'
              if (hasTasks) {
                if (rate >= 1) bgClass = 'bg-moss-100 text-moss-700 hover:bg-moss-200 dark:bg-moss-900/30 dark:text-moss-300 dark:hover:bg-moss-900/40'
                else if (rate >= 0.67) bgClass = 'bg-amber-50 text-amber-700 hover:bg-amber-100 dark:bg-amber-900/20 dark:text-amber-300 dark:hover:bg-amber-900/30'
                else if (rate >= 0.33) bgClass = 'bg-stone-100 text-stone-600 hover:bg-stone-200 dark:bg-stone-700 dark:text-stone-300 dark:hover:bg-stone-600'
                else bgClass = 'bg-terracotta-50 text-terracotta-700 hover:bg-terracotta-100 dark:bg-terracotta-900/20 dark:text-terracotta-300 dark:hover:bg-terracotta-900/30'
              }

              return (
                <button
                  key={dateStr}
                  onClick={() => navigate(`/day/${dateStr}`)}
                  className={`
                    aspect-square flex flex-col items-center justify-center rounded-xl text-sm font-medium
                    transition-all duration-200 cursor-pointer hover:shadow-soft hover:-translate-y-0.5
                    ${bgClass}
                    ${isToday ? 'ring-2 ring-terracotta-500 ring-offset-2 dark:ring-offset-stone-800' : ''}
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
          <div className="mt-8 flex items-center gap-6 text-xs text-stone-500 dark:text-stone-400 max-w-2xl">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-stone-50 border border-stone-200 dark:bg-stone-700/40 dark:border-stone-600" />
              <span>No tasks</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-terracotta-100 dark:bg-terracotta-900/30" />
              <span>&lt;33%</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-stone-100 dark:bg-stone-700" />
              <span>33-67%</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-amber-100 dark:bg-amber-900/20" />
              <span>67-99%</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-moss-100 dark:bg-moss-900/30" />
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
