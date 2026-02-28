import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi, templatesApi, dayApi, type TaskTemplate } from '../api/client'
import { useTimerDisplay } from '../hooks/useTimerDisplay'
import { Sidebar } from '../components/Sidebar'
import { TemplateModal } from '../components/TemplateModal'
import { ScheduleModal } from '../components/ScheduleModal'
import { useMobile } from '../contexts/MobileContext'
import { MobileHeader } from '../components/MobileHeader'
import { BottomTabBar } from '../components/BottomTabBar'

const CATEGORY_LABELS: Record<string, string> = {
  deep_work: 'Deep Work',
  short_task: 'Short Task',
  maintenance: 'Maintenance',
}

const CATEGORY_COLORS: Record<string, string> = {
  deep_work: 'bg-ocean-100 text-ocean-700 dark:bg-ocean-900/30 dark:text-ocean-300',
  short_task: 'bg-terracotta-100 text-terracotta-700 dark:bg-terracotta-900/30 dark:text-terracotta-300',
  maintenance: 'bg-moss-100 text-moss-700 dark:bg-moss-900/30 dark:text-moss-300',
}

const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
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
  const isMobile = useMobile()
  const qc = useQueryClient()
  const [saved, setSaved] = useState(false)
  const [calViewDate, setCalViewDate] = useState(new Date())

  const { data: days = [] } = useQuery({
    queryKey: ['days', 'all'],
    queryFn: dayApi.getAll,
  })

  // Template state
  const [templateSearch, setTemplateSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<TaskTemplate | null>(null)
  const [schedulingTemplate, setSchedulingTemplate] = useState<TaskTemplate | null>(null)

  const { data: templates = [], isLoading: templatesLoading } = useQuery({
    queryKey: ['templates', templateSearch],
    queryFn: () => templatesApi.list(templateSearch || undefined),
  })

  const deleteTemplate = useMutation({
    mutationFn: (id: number) => templatesApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['templates'] }),
  })

  const { data: scheduleCounts = {} } = useQuery({
    queryKey: ['schedule-counts', templates.map(t => t.id).join(',')],
    queryFn: async () => {
      const results = await Promise.all(
        templates.map(t => templatesApi.listSchedules(t.id).then(s => [t.id, s.length] as const))
      )
      return Object.fromEntries(results) as Record<number, number>
    },
    enabled: templates.length > 0,
  })

  function openCreate() {
    setEditingTemplate(null)
    setModalOpen(true)
  }

  function openEdit(t: TaskTemplate) {
    setEditingTemplate(t)
    setModalOpen(true)
  }

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

  const { showTimer, toggle: toggleTimer } = useTimerDisplay()

  function toggle(day: string) {
    const next = new Set(recurringDays)
    next.has(day) ? next.delete(day) : next.add(day)
    save.mutate([...next])
  }

  if (isMobile) {
    const year = calViewDate.getFullYear()
    const month = calViewDate.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const startOffset = (firstDay.getDay() + 6) % 7
    const cells: Array<Date | null> = [
      ...Array(startOffset).fill(null),
      ...Array.from({ length: lastDay.getDate() }, (_, i) => new Date(year, month, i + 1)),
    ]
    while (cells.length % 7 !== 0) cells.push(null)
    const todayStr = new Date().toISOString().slice(0, 10)
    const dayMap = new Map(days.map(d => [d.date, d]))

    return (
      <>
      <div className="flex flex-col h-screen bg-stone-900">
        <MobileHeader title="Settings" />
        <div className="flex-1 overflow-y-auto pb-14">
          <div className="px-4 py-4 space-y-8">
            {/* Task Templates card */}
            <div className="rounded-2xl border border-stone-700 bg-stone-800/60 p-6">
              <div className="flex items-center justify-between mb-1">
                <h2 className="text-base font-semibold text-stone-200">
                  Task Templates
                </h2>
                <button
                  type="button"
                  onClick={openCreate}
                  className="w-7 h-7 flex items-center justify-center rounded-lg text-stone-400 hover:text-stone-200 hover:bg-stone-700 transition-colors"
                  aria-label="Add template"
                >
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
                    <path d="M7 2v10M2 7h10" />
                  </svg>
                </button>
              </div>
              <p className="text-sm text-stone-500 mb-4">
                Reusable task blueprints you can quickly add to your day.
              </p>

              {/* Search */}
              <input
                type="text"
                value={templateSearch}
                onChange={e => setTemplateSearch(e.target.value)}
                placeholder="Search templates…"
                className="w-full text-sm border border-stone-600 rounded-lg px-3 py-2 mb-3 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent transition-shadow bg-stone-800 text-stone-100"
              />

              {/* Template list */}
              {templatesLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="h-12 rounded-xl bg-stone-700/40 animate-pulse" />
                  ))}
                </div>
              ) : templates.length === 0 ? (
                <p className="text-sm text-stone-500 text-center py-6">
                  {templateSearch ? 'No templates match your search.' : 'No templates yet. Create one to get started.'}
                </p>
              ) : (
                <div className="space-y-1.5">
                  {templates.map(t => (
                    <div
                      key={t.id}
                      className="group flex items-center gap-3 px-3 py-2.5 rounded-xl border border-stone-600/50 hover:border-stone-500 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-medium text-stone-200 truncate">
                            {t.title}
                          </span>
                          {t.category && (
                            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${CATEGORY_COLORS[t.category]}`}>
                              {CATEGORY_LABELS[t.category]}
                            </span>
                          )}
                          {t.tags.map(tag => (
                            <span key={tag} className="text-xs text-stone-500">
                              #{tag}
                            </span>
                          ))}
                        </div>
                        {t.description && (
                          <p className="text-xs text-stone-500 truncate mt-0.5">{t.description}</p>
                        )}
                      </div>

                      {/* Hover actions */}
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          type="button"
                          onClick={() => setSchedulingTemplate(t)}
                          className="w-7 h-7 flex items-center justify-center rounded-lg text-stone-400 hover:text-moss-400 hover:bg-moss-900/20 transition-colors relative"
                          aria-label={`Schedules for ${t.title}`}
                        >
                          <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
                            <circle cx="6.5" cy="6.5" r="5" />
                            <path d="M6.5 4v2.5l1.5 1.5" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                          {(scheduleCounts[t.id] ?? 0) > 0 && (
                            <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-moss-500 text-white text-[8px] font-bold flex items-center justify-center">
                              {scheduleCounts[t.id]}
                            </span>
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={() => openEdit(t)}
                          className="w-7 h-7 flex items-center justify-center rounded-lg text-stone-400 hover:text-stone-200 hover:bg-stone-600 transition-colors"
                          aria-label={`Edit ${t.title}`}
                        >
                          <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                            <path d="M9 2l2 2L4 11H2V9L9 2z" />
                          </svg>
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            if (confirm(`Delete template "${t.title}"?`)) {
                              deleteTemplate.mutate(t.id)
                            }
                          }}
                          className="w-7 h-7 flex items-center justify-center rounded-lg text-stone-400 hover:text-terracotta-400 hover:bg-terracotta-900/20 transition-colors"
                          aria-label={`Delete ${t.title}`}
                        >
                          <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                            <path d="M2 3h9M5 3V2h3v1M4 3v7a1 1 0 001 1h3a1 1 0 001-1V3" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recurring Days Off card */}
            <div className="rounded-2xl border border-stone-700 bg-stone-800/60 p-6">
              <div className="flex items-center justify-between mb-1">
                <h2 className="text-base font-semibold text-stone-200">
                  Recurring days off
                </h2>
                <span
                  className={`text-xs font-medium text-moss-400 transition-opacity duration-300 ${
                    saved ? 'opacity-100' : 'opacity-0'
                  }`}
                >
                  Saved
                </span>
              </div>
              <p className="text-sm text-stone-500 mb-5">
                These weekdays are automatically marked as off in the calendar.
              </p>

              {isLoading ? (
                <div className="flex gap-2">
                  {DAYS.map(d => (
                    <div key={d} className="h-9 w-12 rounded-xl bg-stone-700/40 animate-pulse" />
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
                            : 'bg-stone-700/60 text-stone-400 hover:bg-stone-700'
                          }`}
                      >
                        {LABELS[day]}
                      </button>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Focus Timer card */}
            <div className="rounded-2xl border border-stone-700 bg-stone-800/60 p-6">
              <h2 className="text-base font-semibold text-stone-200 mb-1">
                Display Focus Timer?
              </h2>
              <p className="text-sm text-stone-500 mb-4">
                Show or hide the focus timer in the sidebar and mobile strip.
              </p>
              <button
                type="button"
                onClick={() => toggleTimer.mutate(!showTimer)}
                className={`px-4 py-2 text-sm font-medium rounded-xl transition-all duration-150
                  ${showTimer
                    ? 'bg-terracotta-500 text-white shadow-glow'
                    : 'bg-stone-700/60 text-stone-400 hover:bg-stone-700'
                  }`}
              >
                {showTimer ? 'On' : 'Off'}
              </button>
            </div>
          </div>

          {/* Calendar section */}
          <div className="px-4 py-4 border-t border-stone-700/50">
            <h2 className="text-xs font-semibold text-stone-400 uppercase tracking-wider mb-4">
              Calendar
            </h2>
            {/* Month navigation */}
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-stone-200">
                {calViewDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
              </span>
              <div className="flex gap-1">
                <button
                  onClick={() => setCalViewDate(new Date(year, month - 1, 1))}
                  className="w-7 h-7 flex items-center justify-center text-stone-400 hover:text-stone-200 hover:bg-stone-700 rounded transition-colors"
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M8 2L4 6L8 10" />
                  </svg>
                </button>
                <button
                  onClick={() => setCalViewDate(new Date(year, month + 1, 1))}
                  className="w-7 h-7 flex items-center justify-center text-stone-400 hover:text-stone-200 hover:bg-stone-700 rounded transition-colors"
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
                <div key={i} className="text-center text-[10px] text-stone-400 font-medium py-1">{d}</div>
              ))}
            </div>
            {/* Calendar grid */}
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

                let bgClass = 'text-stone-400'
                if (hasTasks) {
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
                      transition-all duration-150 hover:bg-stone-600/70
                      ${bgClass}
                      ${isToday ? 'ring-2 ring-terracotta-500 ring-offset-1 ring-offset-stone-850' : ''}
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
          </div>
        </div>
        <BottomTabBar />
      </div>

      {modalOpen && (
        <TemplateModal
          template={editingTemplate}
          onClose={() => setModalOpen(false)}
        />
      )}
      {schedulingTemplate && (
        <ScheduleModal
          template={schedulingTemplate}
          onClose={() => setSchedulingTemplate(null)}
        />
      )}
      </>
    )
  }

  return (
    <>
    <div className="flex h-screen overflow-hidden bg-stone-25 dark:bg-stone-900">
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

          {/* Task Templates card */}
          <div className="rounded-2xl border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-800/60 p-6 mb-6">
            <div className="flex items-center justify-between mb-1">
              <h2 className="text-base font-semibold text-stone-700 dark:text-stone-200">
                Task Templates
              </h2>
              <button
                type="button"
                onClick={openCreate}
                className="w-7 h-7 flex items-center justify-center rounded-lg text-stone-400 hover:text-stone-600 hover:bg-stone-100 dark:hover:text-stone-200 dark:hover:bg-stone-700 transition-colors"
                aria-label="Add template"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
                  <path d="M7 2v10M2 7h10" />
                </svg>
              </button>
            </div>
            <p className="text-sm text-stone-400 dark:text-stone-500 mb-4">
              Reusable task blueprints you can quickly add to your day.
            </p>

            {/* Search */}
            <input
              type="text"
              value={templateSearch}
              onChange={e => setTemplateSearch(e.target.value)}
              placeholder="Search templates…"
              className="w-full text-sm border border-stone-200 rounded-lg px-3 py-2 mb-3 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent transition-shadow dark:bg-stone-800 dark:border-stone-600 dark:text-stone-100"
            />

            {/* Template list */}
            {templatesLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-12 rounded-xl bg-stone-100 dark:bg-stone-700/40 animate-pulse" />
                ))}
              </div>
            ) : templates.length === 0 ? (
              <p className="text-sm text-stone-400 dark:text-stone-500 text-center py-6">
                {templateSearch ? 'No templates match your search.' : 'No templates yet. Create one to get started.'}
              </p>
            ) : (
              <div className="space-y-1.5">
                {templates.map(t => (
                  <div
                    key={t.id}
                    className="group flex items-center gap-3 px-3 py-2.5 rounded-xl border border-stone-100 dark:border-stone-600/50 hover:border-stone-200 dark:hover:border-stone-500 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-medium text-stone-700 dark:text-stone-200 truncate">
                          {t.title}
                        </span>
                        {t.category && (
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${CATEGORY_COLORS[t.category]}`}>
                            {CATEGORY_LABELS[t.category]}
                          </span>
                        )}
                        {t.tags.map(tag => (
                          <span key={tag} className="text-xs text-stone-400 dark:text-stone-500">
                            #{tag}
                          </span>
                        ))}
                      </div>
                      {t.description && (
                        <p className="text-xs text-stone-400 dark:text-stone-500 truncate mt-0.5">{t.description}</p>
                      )}
                    </div>

                    {/* Hover actions */}
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        type="button"
                        onClick={() => setSchedulingTemplate(t)}
                        className="w-7 h-7 flex items-center justify-center rounded-lg text-stone-400 hover:text-moss-600 hover:bg-moss-50 dark:hover:text-moss-400 dark:hover:bg-moss-900/20 transition-colors relative"
                        aria-label={`Schedules for ${t.title}`}
                      >
                        <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
                          <circle cx="6.5" cy="6.5" r="5" />
                          <path d="M6.5 4v2.5l1.5 1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        {(scheduleCounts[t.id] ?? 0) > 0 && (
                          <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-moss-500 text-white text-[8px] font-bold flex items-center justify-center">
                            {scheduleCounts[t.id]}
                          </span>
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={() => openEdit(t)}
                        className="w-7 h-7 flex items-center justify-center rounded-lg text-stone-400 hover:text-stone-600 hover:bg-stone-100 dark:hover:text-stone-200 dark:hover:bg-stone-600 transition-colors"
                        aria-label={`Edit ${t.title}`}
                      >
                        <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <path d="M9 2l2 2L4 11H2V9L9 2z" />
                        </svg>
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          if (confirm(`Delete template "${t.title}"?`)) {
                            deleteTemplate.mutate(t.id)
                          }
                        }}
                        className="w-7 h-7 flex items-center justify-center rounded-lg text-stone-400 hover:text-terracotta-600 hover:bg-terracotta-50 dark:hover:text-terracotta-400 dark:hover:bg-terracotta-900/20 transition-colors"
                        aria-label={`Delete ${t.title}`}
                      >
                        <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <path d="M2 3h9M5 3V2h3v1M4 3v7a1 1 0 001 1h3a1 1 0 001-1V3" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
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

          {/* Focus Timer card */}
          <div className="rounded-2xl border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-800/60 p-6 mt-6">
            <h2 className="text-base font-semibold text-stone-700 dark:text-stone-200 mb-1">
              Display Focus Timer?
            </h2>
            <p className="text-sm text-stone-400 dark:text-stone-500 mb-4">
              Show or hide the focus timer in the sidebar and mobile strip.
            </p>
            <button
              type="button"
              onClick={() => toggleTimer.mutate(!showTimer)}
              className={`px-4 py-2 text-sm font-medium rounded-xl transition-all duration-150
                ${showTimer
                  ? 'bg-terracotta-500 text-white shadow-glow'
                  : 'bg-stone-100 text-stone-500 hover:bg-stone-200 dark:bg-stone-700/60 dark:text-stone-400 dark:hover:bg-stone-700'
                }`}
            >
              {showTimer ? 'On' : 'Off'}
            </button>
          </div>
        </div>
      </main>
    </div>

    {modalOpen && (
      <TemplateModal
        template={editingTemplate}
        onClose={() => setModalOpen(false)}
      />
    )}
    {schedulingTemplate && (
      <ScheduleModal
        template={schedulingTemplate}
        onClose={() => setSchedulingTemplate(null)}
      />
    )}
    </>
  )
}
