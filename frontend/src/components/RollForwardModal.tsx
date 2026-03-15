import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { dayApi, settingsApi, type DayResponse } from '../api/client'

interface Props {
  onConfirm: (targetDate: string) => void
  onCancel: () => void
}

function formatMonth(date: Date): string {
  return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
}

function formatRollDate(isoDate: string): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  const d = new Date(year, month - 1, day)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

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

export function RollForwardModal({ onConfirm, onCancel }: Props) {
  const today = new Date()
  const todayStr = today.toISOString().slice(0, 10)

  const [viewDate, setViewDate] = useState(() => {
    const d = new Date()
    d.setDate(d.getDate() + 1)
    return new Date(d.getFullYear(), d.getMonth(), 1)
  })
  const [selectedDate, setSelectedDate] = useState('')

  const { data: days = [] } = useQuery({
    queryKey: ['days', 'all'],
    queryFn: dayApi.getAll,
  })

  const { data: recurringConfig } = useQuery({
    queryKey: ['settings', 'recurring-days-off'],
    queryFn: settingsApi.getRecurringDaysOff,
    staleTime: 5 * 60 * 1000,
  })

  const recurringOffDays = new Set(recurringConfig?.days ?? [])
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

  function prevMonth() {
    setViewDate(d => new Date(d.getFullYear(), d.getMonth() - 1, 1))
  }

  function nextMonth() {
    setViewDate(d => new Date(d.getFullYear(), d.getMonth() + 1, 1))
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onCancel}>
      <div
        className="bg-stone-800 rounded-2xl shadow-xl p-5 w-96 space-y-4"
        onClick={e => e.stopPropagation()}
      >
        <h2 className="text-sm font-semibold text-stone-200">Roll forward to…</h2>

        {/* Month navigation */}
        <div className="flex items-center justify-between px-1">
          <span className="text-sm font-medium text-stone-100">{formatMonth(viewDate)}</span>
          <div className="flex gap-1">
            <button
              type="button"
              onClick={prevMonth}
              className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-white hover:bg-stone-700 rounded transition-colors"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 2L4 6L8 10" />
              </svg>
            </button>
            <button
              type="button"
              onClick={nextMonth}
              className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-white hover:bg-stone-700 rounded transition-colors"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 2L8 6L4 10" />
              </svg>
            </button>
          </div>
        </div>

        {/* Day-of-week headers */}
        <div className="grid grid-cols-7 gap-1">
          {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d, i) => (
            <div key={i} className="text-center text-[10px] text-stone-400 font-medium py-1">
              {d}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="grid grid-cols-7 gap-1">
          {cells.map((cellDate, i) => {
            if (!cellDate) return <div key={i} className="aspect-square" />

            const dateStr = cellDate.toISOString().slice(0, 10)
            const isPast = dateStr <= todayStr
            const dayData = dayMap.get(dateStr)
            const allTasks = dayData?.tasks ?? []
            const tasks = allTasks.filter(t => t.status !== 'rolled_forward')
            const dayOff = dayData?.day_off ?? null
            const weekdayName = cellDate.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase()
            const isRecurringOff = recurringOffDays.has(weekdayName)
            const isOff = !!dayOff || isRecurringOff
            const offReason = dayOff?.reason ?? (isRecurringOff ? 'weekend' : null)
            const completed = tasks.filter(t => t.status === 'completed').length
            const rate = tasks.length > 0 ? completed / tasks.length : 0
            const hasTasks = tasks.length > 0
            const isSelected = dateStr === selectedDate

            if (isPast) {
              return (
                <div
                  key={dateStr}
                  className="aspect-square flex flex-col items-center justify-center rounded-md text-[11px] font-medium text-stone-600 opacity-40 cursor-not-allowed"
                >
                  <span>{cellDate.getDate()}</span>
                </div>
              )
            }

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
                type="button"
                onClick={() => setSelectedDate(prev => prev === dateStr ? '' : dateStr)}
                className={`
                  aspect-square flex flex-col items-center justify-center rounded-md text-[11px] font-medium
                  transition-all duration-150 cursor-pointer hover:bg-stone-600/70
                  ${bgClass}
                  ${isSelected ? 'ring-2 ring-terracotta-500 ring-offset-1 ring-offset-stone-800' : ''}
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

        {/* Actions */}
        <div className="flex gap-2 pt-1">
          <button
            type="button"
            disabled={!selectedDate}
            onClick={() => onConfirm(selectedDate)}
            className="flex-1 text-sm bg-stone-700 text-white rounded-lg px-4 py-2 hover:bg-stone-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {selectedDate ? `Roll Forward → ${formatRollDate(selectedDate)}` : 'Roll Forward'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="text-sm text-stone-400 hover:text-stone-200 transition-colors px-3"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
