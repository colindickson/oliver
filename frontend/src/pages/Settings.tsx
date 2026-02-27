import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '../api/client'
import { Sidebar } from '../components/Sidebar'

const DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
const LABELS: Record<string, string> = {
  sunday: 'Sun',
  monday: 'Mon',
  tuesday: 'Tue',
  wednesday: 'Wed',
  thursday: 'Thu',
  friday: 'Fri',
  saturday: 'Sat',
}

export function Settings() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [saved, setSaved] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['settings', 'recurring-days-off'],
    queryFn: settingsApi.getRecurringDaysOff,
  })
  const recurringDays = new Set(data?.days ?? [])

  const save = useMutation({
    mutationFn: settingsApi.setRecurringDaysOff,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['settings', 'recurring-days-off'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 1500)
    },
  })

  function toggle(day: string) {
    const next = new Set(recurringDays)
    next.has(day) ? next.delete(day) : next.add(day)
    save.mutate([...next])
  }

  return (
    <div className="flex h-screen overflow-hidden bg-stone-25 dark:bg-stone-800">
      <Sidebar />

      <main className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto px-8 py-8">
          {/* Header */}
          <div className="flex items-center gap-3 mb-8">
            <button
              onClick={() => navigate(-1)}
              className="w-8 h-8 flex items-center justify-center rounded-lg text-stone-400 hover:text-stone-600 hover:bg-stone-100 dark:hover:text-stone-200 dark:hover:bg-stone-700 transition-colors"
              aria-label="Go back"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10 3L5 8L10 13" />
              </svg>
            </button>
            <h1 className="font-display text-2xl font-semibold text-stone-800 dark:text-stone-100 tracking-tight">
              Settings
            </h1>
          </div>

          {/* Recurring Days Off card */}
          <div className="rounded-2xl border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-800/60 p-6">
            <div className="flex items-center justify-between mb-1">
              <h2 className="text-base font-semibold text-stone-700 dark:text-stone-200">
                Recurring days off
              </h2>
              <span
                className={`text-xs font-medium text-moss-600 dark:text-moss-400 transition-opacity duration-300 ${
                  saved ? 'opacity-100' : 'opacity-0'
                }`}
              >
                Saved
              </span>
            </div>
            <p className="text-sm text-stone-400 dark:text-stone-500 mb-5">
              These weekdays are automatically marked as off in the calendar.
            </p>

            {isLoading ? (
              <div className="flex gap-2">
                {DAYS.map(d => (
                  <div key={d} className="h-9 w-12 rounded-xl bg-stone-100 dark:bg-stone-700/40 animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="flex gap-2 flex-wrap">
                {DAYS.map(day => {
                  const active = recurringDays.has(day)
                  return (
                    <button
                      key={day}
                      onClick={() => toggle(day)}
                      className={`px-4 py-2 text-sm font-medium rounded-xl transition-all duration-150
                        ${active
                          ? 'bg-terracotta-500 text-white shadow-glow'
                          : 'bg-stone-100 text-stone-500 hover:bg-stone-200 dark:bg-stone-700/60 dark:text-stone-400 dark:hover:bg-stone-700'
                        }`}
                    >
                      {LABELS[day]}
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
