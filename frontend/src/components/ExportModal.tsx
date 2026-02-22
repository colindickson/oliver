import { useState, useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { dayApi, timerApi } from '../api/client'
import type { TimerSession } from '../api/client'
import { buildExportData, downloadJson, generateExportFilename, getWeekBounds } from '../utils/export'

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

  // Handle Escape key
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose()
    }
  }, [onClose])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  // Calculate date range based on period type
  function getDateRange(type: PeriodType, initial?: string, from?: string, to?: string): { from: string; to: string } {
    const baseDate = initial ? new Date(initial + 'T00:00:00') : new Date()

    switch (type) {
      case 'day':
        const dayStr = initial ?? new Date().toISOString().slice(0, 10)
        return { from: dayStr, to: dayStr }
      case 'week':
        const bounds = getWeekBounds(baseDate)
        return { from: bounds.start, to: bounds.end }
      case 'custom':
        return { from: from ?? '', to: to ?? '' }
    }
  }

  const dateRange = getDateRange(periodType, initialDate, customFrom, customTo)

  // Get preview stats
  const previewDays = days.filter(d => d.date >= dateRange.from && d.date <= dateRange.to)
  const previewStats = {
    dayCount: previewDays.length,
    taskCount: previewDays.flatMap(d => d.tasks).length,
    completedCount: previewDays.flatMap(d => d.tasks).filter(t => t.status === 'completed').length,
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
        role="dialog"
        aria-modal="true"
        aria-labelledby="export-modal-title"
        className="bg-white rounded-2xl shadow-soft-lg p-6 w-full max-w-sm mx-4 animate-slide-up"
        onClick={handleDialogClick}
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-ocean-100 flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="#0369a1" strokeWidth="1.5" aria-hidden="true">
              <path d="M10 2v10M6 8l4 4 4-4" />
              <path d="M3 14v2a1 1 0 001 1h12a1 1 0 001-1v-2" />
            </svg>
          </div>
          <h2 id="export-modal-title" className="text-base font-semibold text-stone-800">Export Tasks</h2>
        </div>

        {/* Period Selection */}
        <div className="mb-5">
          <label className="text-xs font-medium text-stone-500 uppercase tracking-wider block mb-2">
            Export Period
          </label>
          <div className="flex gap-2" role="radiogroup" aria-label="Export period">
            {(['day', 'week', 'custom'] as const).map(type => (
              <button
                key={type}
                onClick={() => setPeriodType(type)}
                role="radio"
                aria-checked={periodType === type}
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
              <label htmlFor="export-date-from" className="text-xs font-medium text-stone-500 uppercase tracking-wider block mb-2">
                From
              </label>
              <input
                id="export-date-from"
                type="date"
                value={customFrom}
                onChange={e => setCustomFrom(e.target.value)}
                className="w-full text-sm border border-stone-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-ocean-300 focus:border-transparent transition-shadow"
              />
            </div>
            <div>
              <label htmlFor="export-date-to" className="text-xs font-medium text-stone-500 uppercase tracking-wider block mb-2">
                To
              </label>
              <input
                id="export-date-to"
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
            {previewStats.dayCount} {previewStats.dayCount === 1 ? 'day' : 'days'} - {previewStats.taskCount} tasks - {previewStats.taskCount > 0 ? Math.round((previewStats.completedCount / previewStats.taskCount) * 100) : 0}% complete
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
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Exporting...
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
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
