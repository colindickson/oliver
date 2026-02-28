import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi, templatesApi, type TaskTemplate } from '../api/client'
import { Sidebar } from '../components/Sidebar'
import { TemplateModal } from '../components/TemplateModal'
import { ScheduleModal } from '../components/ScheduleModal'

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
  const qc = useQueryClient()
  const [saved, setSaved] = useState(false)

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

  function toggle(day: string) {
    const next = new Set(recurringDays)
    next.has(day) ? next.delete(day) : next.add(day)
    save.mutate([...next])
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
