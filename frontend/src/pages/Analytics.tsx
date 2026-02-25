import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart, Line,
  BarChart, Bar,
  PieChart, Pie, Cell,
  AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { analyticsApi, dayApi } from '../api/client'
import type { CategoryEntry, DayResponse } from '../api/client'
import { Sidebar } from '../components/Sidebar'
import { ExportModal } from '../components/ExportModal'
import { useTheme } from '../contexts/ThemeContext'

// -----------------------------------------------------------------------------
// Chart color palette
// -----------------------------------------------------------------------------

const TERRACOTTA = '#e86b3a'
const OCEAN = '#0c87eb'
const MOSS = '#4a8a4a'
const AMBER = '#f59e0b'

const PIE_COLORS: Record<string, string> = {
  deep_work: OCEAN,
  short_task: TERRACOTTA,
  maintenance: MOSS,
}

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

function formatChartDate(dateStr: string): string {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function xAxisInterval(dataLength: number): number {
  return Math.max(0, Math.floor(dataLength / 8) - 1)
}

// -----------------------------------------------------------------------------
// Data transform types + functions
// -----------------------------------------------------------------------------

interface CompletionRatePoint { date: string; rate: number }
interface TaskVolumePoint { date: string; deep_work: number; short_task: number; maintenance: number }
interface DeepWorkPoint { date: string; deep_work: number }
interface RatingPoint { date: string; focus: number | null; energy: number | null; satisfaction: number | null }

function filterDaysToWindow(days: DayResponse[], windowDays: number): DayResponse[] {
  const cutoff = new Date()
  cutoff.setDate(cutoff.getDate() - windowDays)
  const cutoffStr = cutoff.toISOString().slice(0, 10)
  return days
    .filter(d => d.date >= cutoffStr)
    .sort((a, b) => a.date.localeCompare(b.date))
}

function buildCompletionRateData(days: DayResponse[]): CompletionRatePoint[] {
  return days.map(d => {
    const total = d.tasks.length
    const completed = d.tasks.filter(t => t.status === 'completed').length
    return { date: formatChartDate(d.date), rate: total > 0 ? Math.round((completed / total) * 100) : 0 }
  })
}

function buildTaskVolumeData(days: DayResponse[]): TaskVolumePoint[] {
  return days.map(d => ({
    date: formatChartDate(d.date),
    deep_work: d.tasks.filter(t => t.category === 'deep_work').length,
    short_task: d.tasks.filter(t => t.category === 'short_task').length,
    maintenance: d.tasks.filter(t => t.category === 'maintenance').length,
  }))
}

function buildDeepWorkData(days: DayResponse[]): DeepWorkPoint[] {
  return days.map(d => ({
    date: formatChartDate(d.date),
    deep_work: d.tasks.filter(t => t.category === 'deep_work').length,
  }))
}

function buildRatingsData(days: DayResponse[]): RatingPoint[] {
  return days
    .filter(d => d.rating !== null)
    .map(d => ({
      date: formatChartDate(d.date),
      focus: d.rating?.focus ?? null,
      energy: d.rating?.energy ?? null,
      satisfaction: d.rating?.satisfaction ?? null,
    }))
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
    <div className="bg-white dark:bg-stone-800/80 rounded-2xl border border-stone-100 dark:border-stone-700 p-6 shadow-soft">
      <p className="text-xs font-medium text-stone-400 uppercase tracking-wider">{label}</p>
      <p className={`text-3xl font-semibold mt-2 tabular-nums ${accent ? 'text-terracotta-600' : 'text-stone-800 dark:text-stone-100'}`}>
        {value}
      </p>
      {sub && <p className="text-xs text-stone-400 mt-1">{sub}</p>}
    </div>
  )
}

// -----------------------------------------------------------------------------
// Period options
// -----------------------------------------------------------------------------

const PERIODS = [
  { label: '7d', value: 7 as const },
  { label: '30d', value: 30 as const },
  { label: '90d', value: 90 as const },
]

// -----------------------------------------------------------------------------
// Analytics page
// -----------------------------------------------------------------------------

export function Analytics() {
  const [periodDays, setPeriodDays] = useState<7 | 30 | 90>(7)
  const [showExportModal, setShowExportModal] = useState(false)
  const { theme } = useTheme()

  const isDark = theme === 'dark'
  const gridColor = isDark ? '#292524' : '#e7e5e4'
  const tickColor = isDark ? '#a8a29e' : '#78716c'
  const tooltipStyle = isDark
    ? { backgroundColor: '#1c1917', border: '1px solid #44403c', color: '#e7e5e4', borderRadius: '8px', fontSize: '12px' }
    : { backgroundColor: '#ffffff', border: '1px solid #e7e5e4', color: '#292524', borderRadius: '8px', fontSize: '12px' }

  const { data: summary } = useQuery({
    queryKey: ['analytics', 'summary', periodDays],
    queryFn: () => analyticsApi.getSummary(periodDays),
  })

  const { data: streaks } = useQuery({
    queryKey: ['analytics', 'streaks'],
    queryFn: analyticsApi.getStreaks,
  })

  const { data: categories } = useQuery({
    queryKey: ['analytics', 'categories'],
    queryFn: analyticsApi.getCategories,
  })

  const { data: allDays = [] } = useQuery({
    queryKey: ['days', 'all'],
    queryFn: dayApi.getAll,
  })

  const windowedDays = filterDaysToWindow(allDays, periodDays)
  const completionRateData = buildCompletionRateData(windowedDays)
  const taskVolumeData = buildTaskVolumeData(windowedDays)
  const deepWorkData = buildDeepWorkData(windowedDays)
  const ratingsData = buildRatingsData(windowedDays)

  const pieData = (categories?.entries ?? []).map((e: CategoryEntry) => ({
    name: humanCategory(e.category),
    value: e.total_seconds,
    category: e.category,
  }))

  const chartCard = 'bg-white dark:bg-stone-800/80 rounded-2xl border border-stone-100 dark:border-stone-700 p-6 shadow-soft'
  const sectionHeader = 'text-xs font-semibold text-stone-400 uppercase tracking-wider mb-4'
  const chartTitle = 'text-sm font-medium text-stone-600 dark:text-stone-300 mb-4'
  const emptyChart = 'text-sm text-stone-400 flex items-center justify-center'

  return (
    <div className="flex h-screen overflow-hidden bg-stone-25 dark:bg-stone-800">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-stone-200 dark:bg-stone-800/90 dark:border-stone-700/50 px-8 py-5 flex-shrink-0 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-stone-800 dark:text-stone-100">Analytics</h1>
            <p className="text-sm text-stone-400 mt-0.5">Last {periodDays} days</p>
          </div>
          <div className="flex items-center gap-3">
            {/* Period selector */}
            <div className="flex items-center bg-stone-100 dark:bg-stone-700 rounded-xl p-1 gap-0.5">
              {PERIODS.map(({ label, value }) => (
                <button
                  key={value}
                  onClick={() => setPeriodDays(value)}
                  className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                    periodDays === value
                      ? 'bg-white dark:bg-stone-600 text-stone-800 dark:text-stone-100 shadow-soft'
                      : 'text-stone-500 dark:text-stone-400 hover:text-stone-700 dark:hover:text-stone-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            {/* Export button */}
            <button
              onClick={() => setShowExportModal(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-stone-600 bg-white border border-stone-200 rounded-xl hover:bg-stone-50 hover:border-stone-300 transition-all dark:text-stone-300 dark:bg-stone-700 dark:border-stone-600 dark:hover:bg-stone-600"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M7 1v7M4 5l3 3 3-3" />
                <path d="M1 10v1.5a1 1 0 001 1h10a1 1 0 001-1V10" />
              </svg>
              Export
            </button>
          </div>
        </header>

        <main className="flex-1 p-8 space-y-10 overflow-auto">
          {/* Section: Overview */}
          <section>
            <h2 className={sectionHeader}>Overview</h2>
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
                sub={`in last ${periodDays} days`}
              />
              <SummaryCard
                label="Current streak"
                value={streaks?.current_streak ?? 0}
                sub={
                  streaks?.current_streak === streaks?.longest_streak && (streaks?.current_streak ?? 0) > 0
                    ? 'Personal best!'
                    : `best: ${streaks?.longest_streak ?? 0}`
                }
              />
              <SummaryCard
                label="Longest streak"
                value={streaks?.longest_streak ?? 0}
                sub="days"
              />
            </div>
          </section>

          {/* Section: Trends */}
          <section>
            <h2 className={sectionHeader}>Trends</h2>
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {/* Completion Rate Over Time */}
              <div className={chartCard}>
                <h3 className={chartTitle}>Completion Rate Over Time</h3>
                {completionRateData.length === 0 ? (
                  <div className={`${emptyChart} h-[200px]`}>No data for this period</div>
                ) : (
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={completionRateData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                      <XAxis
                        dataKey="date"
                        tick={{ fill: tickColor, fontSize: 11 }}
                        interval={xAxisInterval(completionRateData.length)}
                      />
                      <YAxis
                        domain={[0, 100]}
                        tickFormatter={v => `${v}%`}
                        tick={{ fill: tickColor, fontSize: 11 }}
                      />
                      <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => [`${v}%`, 'Rate']} />
                      <Line type="monotone" dataKey="rate" stroke={TERRACOTTA} strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Task Volume by Category */}
              <div className={chartCard}>
                <h3 className={chartTitle}>Task Volume by Category</h3>
                {taskVolumeData.length === 0 ? (
                  <div className={`${emptyChart} h-[220px]`}>No data for this period</div>
                ) : (
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={taskVolumeData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                      <XAxis
                        dataKey="date"
                        tick={{ fill: tickColor, fontSize: 11 }}
                        interval={xAxisInterval(taskVolumeData.length)}
                      />
                      <YAxis allowDecimals={false} tick={{ fill: tickColor, fontSize: 11 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="deep_work" name="Deep Work" stackId="a" fill={OCEAN} />
                      <Bar dataKey="short_task" name="Short Task" stackId="a" fill={TERRACOTTA} />
                      <Bar dataKey="maintenance" name="Maintenance" stackId="a" fill={MOSS} radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </section>

          {/* Section: Time Breakdown */}
          <section>
            <h2 className={sectionHeader}>Time Breakdown</h2>
            <div className={`${chartCard} max-w-lg`}>
              {pieData.length === 0 ? (
                <p className="text-sm text-stone-400">No timer sessions recorded yet.</p>
              ) : (
                <div className="flex items-center gap-6">
                  <div className="flex-shrink-0">
                    <PieChart width={200} height={200}>
                      <Pie
                        data={pieData}
                        cx={100}
                        cy={100}
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={2}
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={PIE_COLORS[entry.category] ?? '#78716c'}
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={tooltipStyle}
                        formatter={(v: number) => [formatSeconds(v), '']}
                      />
                    </PieChart>
                  </div>
                  <div className="space-y-3 flex-1 min-w-0">
                    {(categories?.entries ?? []).map((entry: CategoryEntry) => (
                      <div key={entry.category} className="flex items-start gap-2">
                        <div
                          className="w-2.5 h-2.5 rounded-full mt-0.5 flex-shrink-0"
                          style={{ backgroundColor: PIE_COLORS[entry.category] ?? '#78716c' }}
                        />
                        <div className="min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-sm font-medium text-stone-700 dark:text-stone-200 truncate">
                              {humanCategory(entry.category)}
                            </span>
                            <span className="text-xs text-stone-400 flex-shrink-0">
                              {formatSeconds(entry.total_seconds)}
                            </span>
                          </div>
                          <p className="text-xs text-stone-400">
                            {entry.task_count} task{entry.task_count !== 1 ? 's' : ''}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Section: Deep Work */}
          <section>
            <h2 className={sectionHeader}>Deep Work</h2>
            <div className={chartCard}>
              <h3 className={chartTitle}>Deep Work Sessions per Day</h3>
              {deepWorkData.length === 0 ? (
                <div className={`${emptyChart} h-[200px]`}>No data for this period</div>
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={deepWorkData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="deepWorkGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={OCEAN} stopOpacity={0.2} />
                        <stop offset="95%" stopColor={OCEAN} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                    <XAxis
                      dataKey="date"
                      tick={{ fill: tickColor, fontSize: 11 }}
                      interval={xAxisInterval(deepWorkData.length)}
                    />
                    <YAxis allowDecimals={false} tick={{ fill: tickColor, fontSize: 11 }} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <ReferenceLine
                      y={1}
                      stroke={tickColor}
                      strokeDasharray="4 4"
                      label={{ value: 'Goal', fill: tickColor, fontSize: 10 }}
                    />
                    <Area
                      type="monotone"
                      dataKey="deep_work"
                      name="Deep Work"
                      stroke={OCEAN}
                      strokeWidth={2}
                      fill="url(#deepWorkGrad)"
                      dot={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </section>

          {/* Section: Daily Ratings */}
          <section>
            <h2 className={sectionHeader}>Daily Ratings</h2>
            <div className={chartCard}>
              {ratingsData.length === 0 ? (
                <div className="h-[200px] flex flex-col items-center justify-center gap-2 text-stone-400">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M8 15s1.5 2 4 2 4-2 4-2" />
                    <line x1="9" y1="9" x2="9.01" y2="9" strokeWidth="2" />
                    <line x1="15" y1="9" x2="15.01" y2="9" strokeWidth="2" />
                  </svg>
                  <p className="text-sm">No ratings in this period</p>
                  <p className="text-xs opacity-70">Rate your days from the day view to see trends</p>
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-4 mb-4">
                    <div className="flex items-center gap-1.5">
                      <div className="w-3 h-0.5 rounded" style={{ backgroundColor: TERRACOTTA }} />
                      <span className="text-xs text-stone-500 dark:text-stone-400">Focus</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-3 h-0.5 rounded" style={{ backgroundColor: AMBER }} />
                      <span className="text-xs text-stone-500 dark:text-stone-400">Energy</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-3 h-0.5 rounded" style={{ backgroundColor: MOSS }} />
                      <span className="text-xs text-stone-500 dark:text-stone-400">Satisfaction</span>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={ratingsData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                      <XAxis
                        dataKey="date"
                        tick={{ fill: tickColor, fontSize: 11 }}
                        interval={xAxisInterval(ratingsData.length)}
                      />
                      <YAxis domain={[1, 5]} ticks={[1, 2, 3, 4, 5]} tick={{ fill: tickColor, fontSize: 11 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Line type="monotone" dataKey="focus" name="Focus" stroke={TERRACOTTA} strokeWidth={2} dot={false} connectNulls />
                      <Line type="monotone" dataKey="energy" name="Energy" stroke={AMBER} strokeWidth={2} dot={false} connectNulls />
                      <Line type="monotone" dataKey="satisfaction" name="Satisfaction" stroke={MOSS} strokeWidth={2} dot={false} connectNulls />
                    </LineChart>
                  </ResponsiveContainer>
                </>
              )}
            </div>
          </section>
        </main>
      </div>

      {showExportModal && <ExportModal onClose={() => setShowExportModal(false)} />}
    </div>
  )
}
