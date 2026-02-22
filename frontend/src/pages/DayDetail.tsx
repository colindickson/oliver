import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { dayApi } from '../api/client'
import { Sidebar } from '../components/Sidebar'

export function DayDetail() {
  const { date } = useParams<{ date: string }>()
  const navigate = useNavigate()

  const { data: day, isLoading, isError } = useQuery({
    queryKey: ['day', date],
    queryFn: () => dayApi.getByDate(date!),
    enabled: !!date,
  })

  const categories = [
    { key: 'deep_work', label: 'Deep Work', color: 'text-ocean-600', bg: 'bg-ocean-50', border: 'border-ocean-200' },
    { key: 'short_task', label: 'Short Tasks', color: 'text-terracotta-600', bg: 'bg-terracotta-50', border: 'border-terracotta-200' },
    { key: 'maintenance', label: 'Maintenance', color: 'text-moss-600', bg: 'bg-moss-50', border: 'border-moss-200' },
  ] as const

  const completedCount = day?.tasks.filter(t => t.status === 'completed').length ?? 0
  const totalCount = day?.tasks.length ?? 0
  const completionRate = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0

  return (
    <div className="flex min-h-screen bg-stone-25">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-stone-200 px-8 py-5 flex items-center justify-between flex-shrink-0">
          <div>
            <button
              onClick={() => navigate('/calendar')}
              className="text-sm text-stone-400 hover:text-stone-600 mb-2 flex items-center gap-1 transition-colors"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10 4L6 8L10 12" />
              </svg>
              Back to Calendar
            </button>
            {day && (
              <h1 className="text-xl font-semibold text-stone-800">
                {new Date(day.date + 'T12:00:00').toLocaleDateString('en-US', {
                  weekday: 'long',
                  month: 'long',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </h1>
            )}
          </div>

          {/* Completion stats */}
          {day && totalCount > 0 && (
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-2xl font-semibold text-stone-800 tabular-nums">
                  {completedCount}<span className="text-stone-400">/{totalCount}</span>
                </p>
                <p className="text-xs text-stone-400">tasks completed</p>
              </div>

              {/* Progress ring */}
              <div className="relative w-12 h-12">
                <svg className="w-12 h-12 -rotate-90" viewBox="0 0 48 48">
                  <circle
                    cx="24"
                    cy="24"
                    r="20"
                    fill="none"
                    stroke="#e7e5e4"
                    strokeWidth="4"
                  />
                  <circle
                    cx="24"
                    cy="24"
                    r="20"
                    fill="none"
                    stroke={completionRate === 100 ? '#4a8a4a' : '#e86b3a'}
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeDasharray={`${completionRate * 1.256} 125.6`}
                    className="transition-all duration-500"
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-stone-600">
                  {completionRate}%
                </span>
              </div>
            </div>
          )}
        </header>

        {/* Content */}
        <main className="flex-1 p-8 max-w-3xl">
          {isLoading && (
            <div className="flex items-center justify-center h-48 text-stone-400 text-sm">
              Loading...
            </div>
          )}

          {isError && (
            <div className="bg-terracotta-50 border border-terracotta-200 rounded-2xl p-6 text-center">
              <p className="text-terracotta-600">No data for this day.</p>
            </div>
          )}

          {day && (
            <div className="space-y-8 animate-fade-in">
              {categories.map(cat => {
                const tasks = day.tasks.filter(t => t.category === cat.key)
                if (tasks.length === 0) return null

                const catCompleted = tasks.filter(t => t.status === 'completed').length

                return (
                  <div key={cat.key}>
                    <div className="flex items-center justify-between mb-3">
                      <h2 className={`text-sm font-semibold uppercase tracking-wide ${cat.color}`}>
                        {cat.label}
                      </h2>
                      <span className="text-xs text-stone-400 tabular-nums">
                        {catCompleted}/{tasks.length}
                      </span>
                    </div>
                    <div className={`space-y-2 rounded-2xl border ${cat.border} ${cat.bg} p-4`}>
                      {tasks.map(task => (
                        <div
                          key={task.id}
                          className="bg-white rounded-xl border border-stone-100 p-4 flex items-center gap-3 shadow-sm"
                        >
                          <div
                            className={`w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center transition-colors ${
                              task.status === 'completed'
                                ? 'bg-moss-500'
                                : 'bg-stone-200'
                            }`}
                          >
                            {task.status === 'completed' && (
                              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="white" strokeWidth="2">
                                <path d="M2 6L5 9L10 3" strokeLinecap="round" strokeLinejoin="round" />
                              </svg>
                            )}
                          </div>
                          <span
                            className={`text-sm transition-colors ${
                              task.status === 'completed'
                                ? 'line-through text-stone-400'
                                : 'text-stone-800'
                            }`}
                          >
                            {task.title}
                          </span>
                          {task.description && (
                            <span className="text-xs text-stone-400 truncate">
                              — {task.description}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}

              {day.tasks.length === 0 && (
                <div className="text-center py-12 text-stone-400">
                  <p className="text-sm">No tasks recorded for this day.</p>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
