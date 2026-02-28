import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, NavLink, useLocation, Link } from 'react-router-dom'
import { dayApi, settingsApi, type DayResponse, type Task } from '../api/client'
import { SidebarTimer } from './SidebarTimer'
import { useTheme } from '../contexts/ThemeContext'
import { useMobile } from '../contexts/MobileContext'

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
// Day-off style map
// -----------------------------------------------------------------------------

const DAY_OFF_STYLES: Record<string, string> = {
  weekend:      'text-stone-500',
  personal_day: 'bg-purple-500/15 text-purple-300',
  vacation:     'bg-sky-500/15 text-sky-300',
  holiday:      'bg-amber-500/15 text-amber-300',
  sick_day:     'bg-rose-500/15 text-rose-300',
}

const DAY_OFF_LABELS: Record<string, string> = {
  weekend:      'off',
  personal_day: 'personal',
  vacation:     'vacation',
  holiday:      'holiday',
  sick_day:     'sick',
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
// Sidebar
// -----------------------------------------------------------------------------

export function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const [viewDate, setViewDate] = useState(new Date())
  const { theme, toggleTheme } = useTheme()
  const isMobile = useMobile()

  const { data: days = [] } = useQuery({
    queryKey: ['days', 'all'],
    queryFn: dayApi.getAll,
  })

  const { data: recurringConfig } = useQuery({
    queryKey: ['settings', 'recurring-days-off'],
    queryFn: settingsApi.getRecurringDaysOff,
    staleTime: 5 * 60 * 1000,
  })

  // All hooks called above — safe to early return now
  if (isMobile) return null

  const recurringOffDays = new Set(recurringConfig?.days ?? [])

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

  const selectedDateStr = location.pathname.startsWith('/day/')
    ? location.pathname.slice(5)
    : null

  return (
    <aside className="w-72 h-screen bg-stone-850 text-white flex flex-col flex-shrink-0 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-5 border-b border-stone-700/50">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-2xl font-semibold tracking-tight text-white">Oliver</h1>
            <p className="text-xs text-stone-300 mt-0.5">3-3-3 Technique</p>
          </div>
          <div className="flex items-center gap-1">
          <Link
            to="/settings"
            className={`w-7 h-7 flex items-center justify-center rounded-lg transition-colors flex-shrink-0
              ${location.pathname === '/settings'
                ? 'text-stone-200 bg-stone-700'
                : 'text-stone-400 hover:text-stone-200 hover:bg-stone-700'
              }`}
            aria-label="Settings"
          >
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor"
                 strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="1" y1="3.5" x2="14" y2="3.5" />
              <circle cx="5" cy="3.5" r="1.5" fill="currentColor" stroke="none" />
              <line x1="1" y1="7.5" x2="14" y2="7.5" />
              <circle cx="10" cy="7.5" r="1.5" fill="currentColor" stroke="none" />
              <line x1="1" y1="11.5" x2="14" y2="11.5" />
              <circle cx="5" cy="11.5" r="1.5" fill="currentColor" stroke="none" />
            </svg>
          </Link>
          <button
            onClick={toggleTheme}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-stone-400 hover:text-stone-200 hover:bg-stone-700 transition-colors flex-shrink-0"
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? (
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                <circle cx="7.5" cy="7.5" r="2.5" />
                <path d="M7.5 1v1.5M7.5 12.5V14M1 7.5h1.5M12.5 7.5H14M3.05 3.05l1.06 1.06M10.9 10.9l1.06 1.06M3.05 11.95l1.06-1.06M10.9 4.1l1.06-1.06" />
              </svg>
            ) : (
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M13 8A5.6 5.6 0 1 1 7 1.9 4.4 4.4 0 0 0 13 8z" />
              </svg>
            )}
          </button>
          </div>
        </div>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto">

      {/* Nav */}
      <nav className="px-3 py-2 border-b border-stone-700/50">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-stone-700 text-white'
                : 'text-stone-300 hover:text-white hover:bg-stone-700/50'
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
          to="/goals"
          className={({ isActive }) =>
            `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-stone-700 text-white'
                : 'text-stone-300 hover:text-white hover:bg-stone-700/50'
            }`
          }
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="7" cy="7" r="6" />
            <circle cx="7" cy="7" r="2.5" />
            <circle cx="7" cy="7" r="0.75" fill="currentColor" stroke="none" />
            <path d="M7 1v1.5M7 11.5V13M1 7h1.5M11.5 7H13" strokeLinecap="round" />
          </svg>
          Goals
        </NavLink>
        <NavLink
          to="/backlog"
          className={({ isActive }) =>
            `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-stone-700 text-white'
                : 'text-stone-300 hover:text-white hover:bg-stone-700/50'
            }`
          }
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M2 2h10v10H2z" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M5 5h4M5 7h4M5 9h2" strokeLinecap="round" />
          </svg>
          Backlog
        </NavLink>
        <NavLink
          to="/tags"
          className={({ isActive }) =>
            `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-stone-700 text-white'
                : 'text-stone-300 hover:text-white hover:bg-stone-700/50'
            }`
          }
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M1 7L7 1h5v5L7 13 1 7Z" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="9.5" cy="4.5" r="1" fill="currentColor" stroke="none" />
          </svg>
          Tags
        </NavLink>
        <NavLink
          to="/analytics"
          className={({ isActive }) =>
            `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-stone-700 text-white'
                : 'text-stone-300 hover:text-white hover:bg-stone-700/50'
            }`
          }
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
            <polyline points="1,10 4,6 7,8 10,3 13,5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Analytics
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
              className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-white hover:bg-stone-700 rounded transition-colors"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 2L4 6L8 10" />
              </svg>
            </button>
            <button
              onClick={() => setViewDate(new Date(year, month + 1, 1))}
              className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-white hover:bg-stone-700 rounded transition-colors"
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
            <div key={i} className="text-center text-[10px] text-stone-300 font-medium py-1">
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
            const isSelected = dateStr === selectedDateStr
            const hasTasks = tasks.length > 0
            const completed = tasks.filter(t => t.status === 'completed').length
            const rate = hasTasks ? completed / tasks.length : 0

            const dayOff = dayData?.day_off ?? null
            const weekdayName = cellDate.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase()
            const isRecurringOff = recurringOffDays.has(weekdayName)
            const isOff = !!dayOff || isRecurringOff
            const offReason = dayOff?.reason ?? (isRecurringOff ? 'weekend' : null)

            let bgClass = 'text-stone-400'
            if (isOff && offReason) {
              bgClass = DAY_OFF_STYLES[offReason] ?? 'text-stone-500'
            } else if (hasTasks) {
              if (rate >= 1) bgClass = 'bg-moss-600/30 text-moss-300'
              else if (rate >= 0.67) bgClass = 'bg-amber-500/20 text-amber-300'
              else if (rate >= 0.33) bgClass = 'bg-stone-600/50 text-stone-300'
              else bgClass = 'bg-terracotta-500/20 text-terracotta-300'
            }

            return (
              <button
                key={dateStr}
                onClick={() => navigate(`/day/${dateStr}`)}
                className={`
                  aspect-square flex flex-col items-center justify-center rounded-md text-[11px] font-medium
                  transition-all duration-150 cursor-pointer hover:bg-stone-600/70
                  ${bgClass}
                  ${isToday ? 'ring-2 ring-terracotta-500 ring-offset-1 ring-offset-stone-850' : isSelected ? 'ring-2 ring-sky-400/70 ring-offset-1 ring-offset-stone-850' : ''}
                `}
              >
                <span>{cellDate.getDate()}</span>
                {isOff && offReason ? (
                  <span className="text-[8px] opacity-60">{DAY_OFF_LABELS[offReason]}</span>
                ) : hasTasks ? (
                  <span className="text-[8px] opacity-60">{completed}/{tasks.length}</span>
                ) : null}
              </button>
            )
          })}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 mt-3 px-1 text-[10px] text-stone-300">
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


      </div>{/* end scrollable content */}

      {/* Timer - always visible at bottom */}
      <SidebarTimer />
    </aside>
  )
}
