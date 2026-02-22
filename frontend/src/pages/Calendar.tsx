import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { dayApi } from '../api/client'
import type { DayResponse } from '../api/client'
import { CalendarDay } from '../components/CalendarDay'
import { Sidebar } from '../components/Sidebar'

export function Calendar() {
  const navigate = useNavigate()
  const [viewDate, setViewDate] = useState(new Date())

  const { data: days = [] } = useQuery({
    queryKey: ['days', 'all'],
    queryFn: dayApi.getAll,
  })

  // Build a map: "YYYY-MM-DD" → DayResponse for quick lookup
  const dayMap = new Map<string, DayResponse>(
    days.map(d => [d.date, d])
  )

  const year = viewDate.getFullYear()
  const month = viewDate.getMonth()

  // Build the grid: fill from Monday, get all days in this month
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)

  // Grid starts on Monday (0=Mon, 6=Sun)
  const startOffset = (firstDay.getDay() + 6) % 7  // convert Sun-based to Mon-based
  const cells: Array<Date | null> = [
    ...Array(startOffset).fill(null),
    ...Array.from({ length: lastDay.getDate() }, (_, i) => new Date(year, month, i + 1)),
  ]
  // Pad to complete weeks
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
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-semibold text-gray-900">{monthLabel}</h1>
          <div className="flex gap-2">
            <button onClick={prevMonth} className="px-3 py-1.5 text-sm bg-white border rounded-lg hover:bg-gray-50">
              &lt;
            </button>
            <button onClick={nextMonth} className="px-3 py-1.5 text-sm bg-white border rounded-lg hover:bg-gray-50">
              &gt;
            </button>
          </div>
        </div>

        {/* Day headers */}
        <div className="grid grid-cols-7 gap-1 mb-1">
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => (
            <div key={d} className="text-center text-xs font-medium text-gray-400 py-1">{d}</div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="grid grid-cols-7 gap-1">
          {cells.map((cellDate, i) => {
            if (!cellDate) return <div key={i} />
            const dateStr = cellDate.toISOString().slice(0, 10)
            const dayData = dayMap.get(dateStr)
            const isToday = dateStr === todayStr
            return (
              <CalendarDay
                key={dateStr}
                date={cellDate}
                tasks={dayData?.tasks ?? []}
                isToday={isToday}
                onClick={() => navigate(`/day/${dateStr}`)}
              />
            )
          })}
        </div>

        {/* Legend */}
        <div className="mt-6 flex items-center gap-4 text-xs text-gray-500">
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-gray-50 border" /> No tasks</div>
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-red-100" /> &lt;33%</div>
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-amber-200" /> &lt;67%</div>
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-green-300" /> &lt;100%</div>
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-green-500" /> 100%</div>
        </div>
      </div>
    </div>
  )
}
