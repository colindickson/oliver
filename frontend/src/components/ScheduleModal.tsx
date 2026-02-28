import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { templatesApi, type TaskTemplate, type RecurrenceType } from '../api/client'

const RECURRENCE_LABELS: Record<RecurrenceType, string> = {
  weekly: 'Weekly',
  bi_weekly: 'Bi-weekly',
  monthly: 'Monthly',
}

function tomorrow(): string {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
}

interface Props {
  template: TaskTemplate
  onClose: () => void
}

export function ScheduleModal({ template, onClose }: Props) {
  const qc = useQueryClient()
  const [recurrence, setRecurrence] = useState<RecurrenceType>('weekly')
  const [anchorDate, setAnchorDate] = useState(tomorrow())
  const [error, setError] = useState('')

  const { data: schedules = [], isLoading } = useQuery({
    queryKey: ['schedules', template.id],
    queryFn: () => templatesApi.listSchedules(template.id),
  })

  const create = useMutation({
    mutationFn: () =>
      templatesApi.createSchedule(template.id, { recurrence, anchor_date: anchorDate }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['schedules', template.id] })
      qc.invalidateQueries({ queryKey: ['templates'] })
      setError('')
    },
    onError: () => setError('Failed to create schedule.'),
  })

  const remove = useMutation({
    mutationFn: (scheduleId: number) =>
      templatesApi.deleteSchedule(template.id, scheduleId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['schedules', template.id] })
      qc.invalidateQueries({ queryKey: ['templates'] })
    },
  })

  return (
    <div
      className="fixed inset-0 bg-stone-900/50 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="schedule-modal-title"
        className="bg-white rounded-2xl shadow-soft-lg p-6 w-full max-w-sm mx-4 animate-slide-up dark:bg-stone-700"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-moss-100 dark:bg-moss-900/30 flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-moss-600 dark:text-moss-400" aria-hidden="true">
              <circle cx="9" cy="9" r="7" />
              <path d="M9 5v4l2.5 2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div>
            <h2 id="schedule-modal-title" className="text-base font-semibold text-stone-800 dark:text-stone-100">
              Schedules
            </h2>
            <p className="text-xs text-stone-400 dark:text-stone-500 truncate max-w-[180px]">{template.title}</p>
          </div>
          <button
            onClick={onClose}
            className="ml-auto w-7 h-7 flex items-center justify-center rounded-lg text-stone-400 hover:text-stone-600 hover:bg-stone-100 dark:hover:text-stone-200 dark:hover:bg-stone-600 transition-colors"
            aria-label="Close"
          >
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
              <path d="M2 2l9 9M11 2l-9 9" />
            </svg>
          </button>
        </div>

        {/* Existing schedules */}
        <div className="mb-4">
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2].map(i => (
                <div key={i} className="h-10 rounded-xl bg-stone-100 dark:bg-stone-600/40 animate-pulse" />
              ))}
            </div>
          ) : schedules.length === 0 ? (
            <p className="text-sm text-stone-400 dark:text-stone-500 text-center py-3">
              No schedules yet.
            </p>
          ) : (
            <div className="space-y-1.5">
              {schedules.map(s => (
                <div key={s.id} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-stone-50 dark:bg-stone-800/60 border border-stone-100 dark:border-stone-600/40">
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-stone-700 dark:text-stone-200">
                      {RECURRENCE_LABELS[s.recurrence as RecurrenceType]}
                    </span>
                    <span className="text-xs text-stone-400 dark:text-stone-500 ml-2">
                      starting {s.anchor_date}
                    </span>
                    <div className="text-xs text-stone-400 dark:text-stone-500">
                      next: {s.next_run_date}
                    </div>
                  </div>
                  <button
                    onClick={() => remove.mutate(s.id)}
                    disabled={remove.isPending}
                    className="w-6 h-6 flex items-center justify-center rounded-lg text-stone-300 hover:text-terracotta-500 hover:bg-terracotta-50 dark:hover:text-terracotta-400 dark:hover:bg-terracotta-900/20 transition-colors"
                    aria-label="Delete schedule"
                  >
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" aria-hidden="true">
                      <path d="M2 2l8 8M10 2l-8 8" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="border-t border-stone-100 dark:border-stone-600 mb-4" />

        {/* Add schedule form */}
        <div className="space-y-3">
          <p className="text-xs font-medium text-stone-500 dark:text-stone-400 uppercase tracking-wider">Add schedule</p>

          <div className="flex gap-2">
            <select
              value={recurrence}
              onChange={e => setRecurrence(e.target.value as RecurrenceType)}
              className="flex-1 text-sm border border-stone-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-moss-300 focus:border-transparent transition-shadow dark:bg-stone-800 dark:border-stone-600 dark:text-stone-100"
            >
              {(Object.keys(RECURRENCE_LABELS) as RecurrenceType[]).map(r => (
                <option key={r} value={r}>{RECURRENCE_LABELS[r]}</option>
              ))}
            </select>
            <input
              type="date"
              value={anchorDate}
              onChange={e => setAnchorDate(e.target.value)}
              className="flex-1 text-sm border border-stone-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-moss-300 focus:border-transparent transition-shadow dark:bg-stone-800 dark:border-stone-600 dark:text-stone-100 dark:[color-scheme:dark]"
            />
          </div>

          {error && <p className="text-xs text-terracotta-600 dark:text-terracotta-400">{error}</p>}

          <button
            onClick={() => create.mutate()}
            disabled={create.isPending || !anchorDate}
            className="w-full text-sm bg-stone-800 text-white rounded-lg px-4 py-2 hover:bg-stone-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all dark:bg-stone-600 dark:hover:bg-stone-500"
          >
            {create.isPending ? 'Adding…' : 'Add'}
          </button>
        </div>
      </div>
    </div>
  )
}
