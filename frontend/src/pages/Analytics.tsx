import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/client'
import type { CategoryEntry } from '../api/client'
import { Sidebar } from '../components/Sidebar'

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------

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

// -----------------------------------------------------------------------------
// Sub-components
// -----------------------------------------------------------------------------

interface SummaryCardProps {
  label: string
  value: string | number
  sub?: string
  accent?: boolean
}

function SummaryCard({ label, value, sub, accent }: SummaryCardProps) {
  return (
    <div className="bg-white rounded-2xl border border-stone-100 p-6 shadow-soft">
      <p className="text-xs font-medium text-stone-400 uppercase tracking-wider">{label}</p>
      <p className={`text-3xl font-semibold mt-2 tabular-nums ${accent ? 'text-terracotta-600' : 'text-stone-800'}`}>
        {value}
      </p>
      {sub && <p className="text-xs text-stone-400 mt-1">{sub}</p>}
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
    <div className="flex items-center gap-4">
      <div className="flex-1 bg-stone-100 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm tabular-nums w-12 text-right text-stone-500">{pct}%</span>
    </div>
  )
}

const CATEGORY_COLORS: Record<string, string> = {
  deep_work: 'bg-ocean-500',
  short_task: 'bg-terracotta-500',
  maintenance: 'bg-moss-500',
}

function defaultColor(category: string): string {
  return CATEGORY_COLORS[category] ?? 'bg-stone-400'
}

// -----------------------------------------------------------------------------
// Analytics page
// -----------------------------------------------------------------------------

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
    <div className="flex min-h-screen bg-stone-25">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-stone-200 px-8 py-5 flex-shrink-0">
          <h1 className="text-xl font-semibold text-stone-800">Analytics</h1>
          <p className="text-sm text-stone-400 mt-0.5">Last 30 days</p>
        </header>

        <main className="flex-1 p-8 space-y-8 overflow-auto">
          {isLoading ? (
            <div className="flex items-center justify-center h-48 text-stone-400 text-sm">
              Loading...
            </div>
          ) : (
            <>
              {/* Summary cards */}
              <section>
                <h2 className="text-xs font-semibold text-stone-400 uppercase tracking-wider mb-4">
                  Overview
                </h2>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <SummaryCard
                    label="Completion rate"
                    value={`${summary?.completion_rate_pct ?? 0}%`}
                    sub={`${summary?.completed_tasks ?? 0} of ${summary?.total_tasks ?? 0} tasks`}
                    accent
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
                <h2 className="text-xs font-semibold text-stone-400 uppercase tracking-wider mb-4">
                  Streaks
                </h2>
                <div className="grid grid-cols-2 gap-4 max-w-md">
                  <div className="bg-white rounded-2xl border border-stone-100 p-6 shadow-soft text-center">
                    <p className="text-5xl font-bold text-terracotta-600 tabular-nums">
                      {streaks?.current_streak ?? 0}
                    </p>
                    <p className="text-sm text-stone-400 mt-2">Current streak</p>
                    {streaks?.current_streak === streaks?.longest_streak && (streaks?.current_streak ?? 0) > 0 && (
                      <span className="inline-block mt-2 px-2 py-0.5 text-[10px] font-medium bg-terracotta-100 text-terracotta-600 rounded-full">
                        Best!
                      </span>
                    )}
                  </div>
                  <div className="bg-white rounded-2xl border border-stone-100 p-6 shadow-soft text-center">
                    <p className="text-5xl font-bold text-stone-600 tabular-nums">
                      {streaks?.longest_streak ?? 0}
                    </p>
                    <p className="text-sm text-stone-400 mt-2">Longest streak</p>
                  </div>
                </div>
              </section>

              {/* Category breakdown */}
              <section>
                <h2 className="text-xs font-semibold text-stone-400 uppercase tracking-wider mb-4">
                  Time by category
                </h2>
                {categories?.entries.length === 0 ? (
                  <p className="text-sm text-stone-400">
                    No timer sessions recorded yet.
                  </p>
                ) : (
                  <div className="bg-white rounded-2xl border border-stone-100 p-6 shadow-soft space-y-5 max-w-lg">
                    {categories?.entries.map((entry: CategoryEntry) => (
                      <div key={entry.category}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-stone-700">
                            {humanCategory(entry.category)}
                          </span>
                          <span className="text-xs text-stone-400">
                            {formatSeconds(entry.total_seconds)} · {entry.task_count} task{entry.task_count !== 1 ? 's' : ''}
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
