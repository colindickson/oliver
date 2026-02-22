import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/client'
import type { CategoryEntry } from '../api/client'
import { Sidebar } from '../components/Sidebar'
import { StreakCard } from '../components/StreakCard'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatSeconds(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

function humanCategory(category: string): string {
  return category
    .split('_')
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface SummaryCardProps {
  label: string
  value: string | number
  sub?: string
}

function SummaryCard({ label, value, sub }: SummaryCardProps) {
  return (
    <div className="bg-white border rounded-xl p-5 shadow-sm">
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}

interface BarProps {
  value: number
  max: number
  color: string
}

function Bar({ value, max, color }: BarProps) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 bg-gray-100 rounded-full h-3">
        <div className={`h-3 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm tabular-nums w-12 text-right">{pct}%</span>
    </div>
  )
}

const CATEGORY_COLORS: Record<string, string> = {
  deep_work: 'bg-blue-500',
  short_task: 'bg-amber-400',
  maintenance: 'bg-green-500',
}

function defaultColor(category: string): string {
  return CATEGORY_COLORS[category] ?? 'bg-slate-400'
}

// ---------------------------------------------------------------------------
// Analytics page
// ---------------------------------------------------------------------------

export function Analytics() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => analyticsApi.getSummary(30),
  })

  const { data: streaks, isLoading: streaksLoading } = useQuery({
    queryKey: ['analytics', 'streaks'],
    queryFn: analyticsApi.getStreaks,
  })

  const { data: categories, isLoading: categoriesLoading } = useQuery({
    queryKey: ['analytics', 'categories'],
    queryFn: analyticsApi.getCategories,
  })

  const isLoading = summaryLoading || streaksLoading || categoriesLoading

  const maxSeconds =
    categories?.entries.reduce(
      (acc: number, e: CategoryEntry) => Math.max(acc, e.total_seconds),
      0,
    ) ?? 0

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-8 py-4 flex-shrink-0">
          <h1 className="text-xl font-semibold text-gray-900">Analytics</h1>
          <p className="text-sm text-gray-500 mt-0.5">Last 30 days</p>
        </header>

        <main className="flex-1 p-8 space-y-8">
          {isLoading ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
              Loading...
            </div>
          ) : (
            <>
              {/* Summary cards */}
              <section>
                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                  Overview
                </h2>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <SummaryCard
                    label="Completion rate"
                    value={`${summary?.completion_rate_pct ?? 0}%`}
                    sub={`${summary?.completed_tasks ?? 0} of ${summary?.total_tasks ?? 0} tasks`}
                  />
                  <SummaryCard
                    label="Days tracked"
                    value={summary?.total_days_tracked ?? 0}
                    sub={`in last ${summary?.period_days ?? 30} days`}
                  />
                  <SummaryCard
                    label="Tasks completed"
                    value={summary?.completed_tasks ?? 0}
                  />
                  <SummaryCard
                    label="Total tasks"
                    value={summary?.total_tasks ?? 0}
                  />
                </div>
              </section>

              {/* Streaks */}
              <section>
                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                  Streaks
                </h2>
                <div className="max-w-xs">
                  <StreakCard
                    current={streaks?.current_streak ?? 0}
                    longest={streaks?.longest_streak ?? 0}
                  />
                </div>
              </section>

              {/* Category breakdown */}
              <section>
                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                  Time by category
                </h2>
                {categories?.entries.length === 0 ? (
                  <p className="text-sm text-gray-400">
                    No timer sessions recorded yet.
                  </p>
                ) : (
                  <div className="bg-white border rounded-xl p-5 shadow-sm space-y-4 max-w-lg">
                    {categories?.entries.map((entry: CategoryEntry) => (
                      <div key={entry.category}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-gray-700">
                            {humanCategory(entry.category)}
                          </span>
                          <span className="text-xs text-gray-400">
                            {formatSeconds(entry.total_seconds)} &middot;{' '}
                            {entry.task_count} task{entry.task_count !== 1 ? 's' : ''}
                          </span>
                        </div>
                        <Bar
                          value={entry.total_seconds}
                          max={maxSeconds}
                          color={defaultColor(entry.category)}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </>
          )}
        </main>
      </div>
    </div>
  )
}
