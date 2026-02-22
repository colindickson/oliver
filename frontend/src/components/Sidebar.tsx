import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, NavLink } from 'react-router-dom'
import { dayApi, analyticsApi, type DayResponse, type Task } from '../api/client'
import { SidebarTimer } from './SidebarTimer'

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------

function formatMonth(date: Date): string {
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

function getCompletionRate(tasks: Task[]): number {
  if (tasks.length === 0) return 0
  const completed = tasks.filter(t => t.status === 'completed').length
  return completed / tasks.length
}

// -----------------------------------------------------------------------------
// Mini Calendar Day
// -----------------------------------------------------------------------------

interface MiniDayProps {
  date: Date
  tasks: Task[]
  isToday: boolean
  onClick: () => void
}

function MiniDay({ date, tasks, isToday, onClick }: MiniDayProps) {
  const total = tasks.length
  const rate = getCompletionRate(tasks)
  const hasTasks = total > 0

  let bgClass = 'calendar-day-empty'
  if (hasTasks) {
    if (rate >= 1) bgClass = 'calendar-day-completed'
    else if (rate >= 0.67) bgClass = 'calendar-day-partial'
    else if (rate >= 0.33) bgClass = 'calendar-day-has-tasks'
    else bgClass = 'calendar-day-low'
  }

  return (
    <button
      onClick={hasTasks ? onClick : undefined}
      disabled={!hasTasks}
      className={`calendar-day ${bgClass} ${isToday ? 'calendar-day-today' : ''}`}
    >
      <span>{date.getDate()}</span>
      {hasTasks && (
        <span className="text-[9px] opacity-60">
          {tasks.filter(t => t.status === 'completed').length}/{total}
        </span>
      )}
    </button>
  )
}

// -----------------------------------------------------------------------------
// Stat Card
// -----------------------------------------------------------------------------

interface StatProps {
  label: string
  value: string | number
  sub?: string
  accent?: boolean
}

function Stat({ label, value, sub, accent }: StatProps) {
  return (
    <div className="flex-1 text-center py-3">
      <p className={`text-2xl font-semibold tabular-nums ${accent ? 'text-terracotta-600' : 'text-stone-800'}`}>
        {value}
      </p>
      <p className="text-[11px] text-stone-400 mt-0.5">{label}</p>
      {sub && <p className="text-[10px] text-stone-300">{sub}</p>}
    </div>
  )
}

// -----------------------------------------------------------------------------
// Sidebar
// -----------------------------------------------------------------------------

export function Sidebar() {
  const navigate = useNavigate()
  const [viewDate, setViewDate] = useState(new Date())

  const { data: days = [] } = useQuery({
    queryKey: ['days', 'all'],
    queryFn: dayApi.getAll,
  })

  const { data: streaks } = useQuery({
    queryKey: ['analytics', 'streaks'],
    queryFn: analyticsApi.getStreaks,
  })

  const { data: summary } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => analyticsApi.getSummary(7),
  })

  // Build day map
  const dayMap = new Map<string, DayResponse>(days.map(d => [d.date, d]))

  // Calendar grid
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

  return (
    <aside className="w-72 min-h-screen bg-stone-850 text-white flex flex-col flex-shrink-0 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-5 border-b border-stone-700/50">
        <h1 className="font-display text-2xl font-semibold tracking-tight text-white">
          Oliver
        </h1>
        <p className="text-xs text-stone-400 mt-0.5">3-3-3 Method</p>
      </div>

      {/* Nav */}
      <nav className="px-3 py-2 border-b border-stone-700/50">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-stone-700 text-white'
                : 'text-stone-400 hover:text-white hover:bg-stone-700/50'
            }`
          }
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M1 7L7 1L13 7" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M3 5v7h3v-4h2v4h3V5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Home
        </NavLink>
        <NavLink
          to="/calendar"
          className={({ isActive }) =>
            `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-stone-700 text-white'
                : 'text-stone-400 hover:text-white hover:bg-stone-700/50'
            }`
          }
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="1" y="2" width="12" height="11" rx="1.5" />
            <path d="M1 6h12" />
            <path d="M4 1v2M10 1v2" />
          </svg>
          Calendar
        </NavLink>
      </nav>

      {/* Mini Calendar */}
      <div className="px-4 py-4 border-b border-stone-700/50">
        {/* Month navigation */}
        <div className="flex items-center justify-between mb-3 px-1">
          <h2 className="text-sm font-medium text-stone-200">{formatMonth(viewDate)}</h2>
          <div className="flex gap-1">
            <button
              onClick={() => setViewDate(new Date(year, month - 1, 1))}
              className="w-6 h-6 flex items-center justify-center text-stone-400 hover:text-white hover:bg-stone-700 rounded transition-colors"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 2L4 6L8 10" />
              </svg>
            </button>
            <button
              onClick={() => setViewDate(new Date(year, month + 1, 1))}
              className="w-6 h-6 flex items-center justify-center text-stone-400 hover:text-white hover:bg-stone-700 rounded transition-colors"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 2L8 6L4 10" />
              </svg>
            </button>
          </div>
        </div>

        {/* Day headers */}
        <div className="grid grid-cols-7 gap-1 mb-1">
          {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d, i) => (
            <div key={i} className="text-center text-[10px] text-stone-500 font-medium py-1">
              {d}
            </div>
          ))}
        </div>

        {/* Calendar grid - dark theme version */}
        <div className="grid grid-cols-7 gap-1">
          {cells.map((cellDate, i) => {
            if (!cellDate) return <div key={i} className="aspect-square" />
            const dateStr = cellDate.toISOString().slice(0, 10)
            const dayData = dayMap.get(dateStr)
            const tasks = dayData?.tasks ?? []
            const isToday = dateStr === todayStr
            const hasTasks = tasks.length > 0
            const completed = tasks.filter(t => t.status === 'completed').length
            const rate = hasTasks ? completed / tasks.length : 0

            let bgClass = 'text-stone-600'
            if (hasTasks) {
              if (rate >= 1) bgClass = 'bg-moss-600/30 text-moss-300'
              else if (rate >= 0.67) bgClass = 'bg-amber-500/20 text-amber-300'
              else if (rate >= 0.33) bgClass = 'bg-stone-600/50 text-stone-300'
              else bgClass = 'bg-terracotta-500/20 text-terracotta-300'
            }

            return (
              <button
                key={dateStr}
                onClick={() => hasTasks && navigate(`/day/${dateStr}`)}
                disabled={!hasTasks}
                className={`
                  aspect-square flex flex-col items-center justify-center rounded-md text-[11px] font-medium
                  transition-all duration-150
                  ${bgClass}
                  ${isToday ? 'ring-2 ring-terracotta-500 ring-offset-1 ring-offset-stone-850' : ''}
                  ${hasTasks ? 'hover:bg-stone-600/70 cursor-pointer' : 'cursor-default'}
                `}
              >
                <span>{cellDate.getDate()}</span>
                {hasTasks && (
                  <span className="text-[8px] opacity-60">{completed}/{tasks.length}</span>
                )}
              </button>
            )
          })}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 mt-3 px-1 text-[10px] text-stone-500">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-sm bg-moss-600/30" />
            <span>100%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-sm bg-amber-500/20" />
            <span>67%+</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-sm bg-terracotta-500/20" />
            <span>&lt;33%</span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="px-4 py-4 border-b border-stone-700/50">
        <h3 className="text-xs font-medium text-stone-400 uppercase tracking-wider mb-2 px-1">
          This Week
        </h3>
        <div className="bg-stone-800/50 rounded-xl overflow-hidden">
          <div className="flex divide-x divide-stone-700/50">
            <Stat
              label="Streak"
              value={streaks?.current_streak ?? 0}
              sub={streaks?.current_streak === streaks?.longest_streak ? 'best!' : `best: ${streaks?.longest_streak ?? 0}`}
              accent
            />
            <Stat
              label="Done"
              value={summary?.completed_tasks ?? 0}
              sub={`of ${summary?.total_tasks ?? 0}`}
            />
            <Stat
              label="Rate"
              value={`${summary?.completion_rate_pct ?? 0}%`}
            />
          </div>
        </div>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Timer - sticky at bottom */}
      <SidebarTimer />
    </aside>
  )
}
