import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ComposedChart, Line, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { analyticsApi, dayApi } from '../api/client'
import type { DayResponse } from '../api/client'
import { Sidebar } from '../components/Sidebar'
import { ExportModal } from '../components/ExportModal'
import { useTheme } from '../contexts/ThemeContext'
import { useMobile } from '../contexts/MobileContext'
import { MobileHeader } from '../components/MobileHeader'
import { BottomTabBar } from '../components/BottomTabBar'

// -----------------------------------------------------------------------------
// Chart color palette
// -----------------------------------------------------------------------------

const TERRACOTTA = '#e86b3a'
const OCEAN = '#0c87eb'
const MOSS = '#4a8a4a'
const AMBER = '#f59e0b'

// -----------------------------------------------------------------------------
// Environment icon maps
// -----------------------------------------------------------------------------

const WEATHER_ICONS: Record<string, string> = {
  sunny: '☀️',
  partly_cloudy: '⛅',
  cloudy: '☁️',
  rainy: '🌧️',
  snowy: '❄️',
  stormy: '⛈️',
  foggy: '🌫️',
}

const MOON_ICONS: Record<string, string> = {
  new_moon: '🌑',
  waxing_crescent: '🌒',
  first_quarter: '🌓',
  waxing_gibbous: '🌔',
  full_moon: '🌕',
  waning_gibbous: '🌖',
  last_quarter: '🌗',
  waning_crescent: '🌘',
}

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------

function formatChartDate(dateStr: string): string {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function xAxisInterval(dataLength: number): number {
  return Math.max(0, Math.floor(dataLength / 8) - 1)
}

// -----------------------------------------------------------------------------
// Data transform types + functions
// -----------------------------------------------------------------------------

interface TrendsPoint {
  date: string
  completionRate: number | null
  energy: number | null
  moonPhase: string | null
  condition: string | null
  temperature: number | null
}

interface TaskVolumePoint { date: string; deep_work: number; short_task: number; maintenance: number }

function filterDaysToWindow(days: DayResponse[], windowDays: number): DayResponse[] {
  const cutoff = new Date()
  cutoff.setDate(cutoff.getDate() - windowDays)
  const cutoffStr = cutoff.toISOString().slice(0, 10)
  const todayStr = new Date().toISOString().slice(0, 10)
  return days
    .filter(d => d.date >= cutoffStr && d.date < todayStr)
    .filter(d => !d.day_off)                      // exclude days marked as off
    .filter(d => d.tasks.length > 0 || d.notes)   // exclude empty days (no tasks AND no note)
    .sort((a, b) => a.date.localeCompare(b.date))
}

function buildTrendsData(days: DayResponse[]): TrendsPoint[] {
  return days.map(d => {
    const total = d.tasks.length
    const completed = d.tasks.filter(t => t.status === 'completed').length
    return {
      date: formatChartDate(d.date),
      completionRate: total > 0 ? Math.round((completed / total) * 100) : null,
      energy: d.rating?.energy ?? null,
      moonPhase: d.day_metadata?.moon_phase ?? null,
      condition: d.day_metadata?.condition ?? null,
      temperature: d.day_metadata?.temperature_c ?? null,
    }
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

// -----------------------------------------------------------------------------
// Custom XAxis tick — shows moon + weather icons below the date label
// -----------------------------------------------------------------------------

interface TrendsTickProps {
  x?: number
  y?: number
  payload?: { value: string }
  index?: number
  trendsData: TrendsPoint[]
  tickColor: string
}

function TrendsTick({ x = 0, y = 0, payload, index = 0, trendsData, tickColor }: TrendsTickProps) {
  const point = trendsData[index]
  const moon = point?.moonPhase ? MOON_ICONS[point.moonPhase] : null
  const weather = point?.condition ? WEATHER_ICONS[point.condition] : null
  const icons = [moon, weather].filter(Boolean).join('')

  return (
    <g transform={`translate(${x},${y})`}>
      <text
        x={0}
        y={0}
        dy={12}
        textAnchor="middle"
        fill={tickColor}
        fontSize={11}
      >
        {payload?.value}
      </text>
      {icons && (
        <text
          x={0}
          y={0}
          dy={26}
          textAnchor="middle"
          fontSize={10}
        >
          {icons}
        </text>
      )}
    </g>
  )
}

// -----------------------------------------------------------------------------
// Custom Tooltip — includes metadata (weather, moon phase, temperature)
// -----------------------------------------------------------------------------

interface TrendsTooltipProps {
  active?: boolean
  payload?: Array<{
    name: string
    value: number
    color: string
  }>
  label?: string
  trendsData: TrendsPoint[]
  isDark: boolean
}

function TrendsTooltip({ active, payload, label, trendsData, isDark }: TrendsTooltipProps) {
  if (!active || !payload || !label) return null

  const point = trendsData.find(p => p.date === label)

  const containerStyle: React.CSSProperties = {
    backgroundColor: isDark ? '#1c1917' : '#ffffff',
    border: `1px solid ${isDark ? '#44403c' : '#e7e5e4'}`,
    borderRadius: '10px',
    padding: '12px 14px',
    fontSize: '12px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
  }

  const hasMetadata = point?.moonPhase || point?.condition || point?.temperature

  return (
    <div style={containerStyle}>
      <div style={{
        color: isDark ? '#a8a29e' : '#78716c',
        fontSize: '11px',
        fontWeight: 500,
        marginBottom: 8,
        paddingBottom: 8,
        borderBottom: `1px solid ${isDark ? '#292524' : '#e7e5e4'}`,
      }}>
        {label}
      </div>
      {payload.map((entry, idx) => (
        <div
          key={idx}
          style={{
            color: isDark ? '#e7e5e4' : '#292524',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 16,
            marginBottom: 4,
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{
              width: 8,
              height: entry.name === 'Energy' ? 8 : 2,
              borderRadius: entry.name === 'Energy' ? 2 : 1,
              backgroundColor: entry.color,
              display: 'inline-block',
            }} />
            {entry.name}
          </span>
          <span style={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
            {entry.name === 'Completion %' ? `${entry.value}%` : entry.value}
          </span>
        </div>
      ))}
      {hasMetadata && (
        <div style={{
          marginTop: 8,
          paddingTop: 8,
          borderTop: `1px solid ${isDark ? '#292524' : '#e7e5e4'}`,
          color: isDark ? '#a8a29e' : '#78716c',
          fontSize: '11px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
            {point?.condition && (
              <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                <span>{WEATHER_ICONS[point.condition]}</span>
                <span style={{ textTransform: 'capitalize' }}>{point.condition.replace('_', ' ')}</span>
              </span>
            )}
            {point?.moonPhase && (
              <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                <span>{MOON_ICONS[point.moonPhase]}</span>
                <span style={{ textTransform: 'capitalize' }}>{point.moonPhase.replace('_', ' ')}</span>
              </span>
            )}
            {point?.temperature !== null && point?.temperature !== undefined && (
              <span>{Math.round(point.temperature)}°C</span>
            )}
          </div>
        </div>
      )}
    </div>
  )
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
  const isMobile = useMobile()

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

  const { data: allDays = [] } = useQuery({
    queryKey: ['days', 'all'],
    queryFn: dayApi.getAll,
  })

  const windowedDays = filterDaysToWindow(allDays, periodDays)
  const trendsData = buildTrendsData(windowedDays)
  const taskVolumeData = buildTaskVolumeData(windowedDays)

  const chartCard = 'bg-white dark:bg-stone-800/80 rounded-2xl border border-stone-100 dark:border-stone-700 p-6 shadow-soft'
  const sectionHeader = 'text-xs font-semibold text-stone-400 uppercase tracking-wider mb-4'
  const chartTitle = 'text-sm font-medium text-stone-600 dark:text-stone-300 mb-4'
  const emptyChart = 'text-sm text-stone-400 flex items-center justify-center'

  if (isMobile) {
    return (
      <div className="flex flex-col h-screen bg-stone-900">
        <MobileHeader title="Analytics" />
        <div className="flex-1 overflow-y-auto pb-14">
          <div className="px-4 py-4 space-y-10">
            {/* Section: Overview */}
            <section>
              <h2 className={sectionHeader}>Overview</h2>
              <div className="grid grid-cols-2 gap-4">
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

            {/* Period selector */}
            <div className="flex items-center bg-stone-100 dark:bg-stone-700 rounded-xl p-1 gap-0.5">
              {PERIODS.map(({ label, value }) => (
                <button
                  key={value}
                  onClick={() => setPeriodDays(value)}
                  className={`flex-1 px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                    periodDays === value
                      ? 'bg-white dark:bg-stone-600 text-stone-800 dark:text-stone-100 shadow-soft'
                      : 'text-stone-500 dark:text-stone-400 hover:text-stone-700 dark:hover:text-stone-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Section: Trends */}
            <section>
              <h2 className={sectionHeader}>Trends</h2>
              <div className="space-y-6">
                {/* Unified Trends Chart: completion rate (line) + energy (bar) + env icons */}
                <div className={chartCard}>
                  <h3 className={chartTitle}>Completion Rate &amp; Energy</h3>
                  <div className="flex items-center gap-4 mb-3">
                    <div className="flex items-center gap-1.5">
                      <div className="w-3 h-0.5 rounded" style={{ backgroundColor: OCEAN }} />
                      <span className="text-xs text-stone-500 dark:text-stone-400">Completion %</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-3 h-3 rounded-sm opacity-70" style={{ backgroundColor: AMBER }} />
                      <span className="text-xs text-stone-500 dark:text-stone-400">Energy (1–5)</span>
                    </div>
                  </div>
                  {trendsData.length === 0 ? (
                    <div className={`${emptyChart} h-[220px]`}>No data for this period</div>
                  ) : (
                    <ResponsiveContainer width="100%" height={260}>
                      <ComposedChart data={trendsData} margin={{ top: 24, right: 16, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                        <XAxis
                          dataKey="date"
                          height={60}
                          interval={xAxisInterval(trendsData.length)}
                          tick={(props) => (
                            <TrendsTick
                              {...props}
                              trendsData={trendsData}
                              tickColor={tickColor}
                            />
                          )}
                        />
                        <YAxis
                          yAxisId="left"
                          domain={[0, 100]}
                          tickFormatter={v => `${v}%`}
                          tick={{ fill: tickColor, fontSize: 11 }}
                        />
                        <YAxis
                          yAxisId="right"
                          orientation="right"
                          domain={[0, 5]}
                          ticks={[1, 2, 3, 4, 5]}
                          tick={{ fill: tickColor, fontSize: 11 }}
                        />
                        <Tooltip
                          content={<TrendsTooltip trendsData={trendsData} isDark={isDark} />}
                        />
                        <Bar
                          yAxisId="right"
                          dataKey="energy"
                          name="Energy"
                          fill={AMBER}
                          opacity={0.7}
                          radius={[3, 3, 0, 0]}
                        />
                        <Line
                          yAxisId="left"
                          type="monotone"
                          dataKey="completionRate"
                          name="Completion %"
                          stroke={OCEAN}
                          strokeWidth={2}
                          dot={false}
                          connectNulls={false}
                        />
                      </ComposedChart>
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
                      <ComposedChart data={taskVolumeData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                        <XAxis
                          dataKey="date"
                          tick={{ fill: tickColor, fontSize: 11 }}
                          interval={xAxisInterval(taskVolumeData.length)}
                        />
                        <YAxis yAxisId="left" allowDecimals={false} tick={{ fill: tickColor, fontSize: 11 }} />
                        <Tooltip contentStyle={tooltipStyle} />
                        <Bar yAxisId="left" dataKey="deep_work" name="Deep Work" stackId="a" fill={OCEAN} />
                        <Bar yAxisId="left" dataKey="short_task" name="Short Task" stackId="a" fill={TERRACOTTA} />
                        <Bar yAxisId="left" dataKey="maintenance" name="Maintenance" stackId="a" fill={MOSS} radius={[3, 3, 0, 0]} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>
            </section>
          </div>
        </div>
        <BottomTabBar />
        {showExportModal && <ExportModal onClose={() => setShowExportModal(false)} />}
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-stone-25 dark:bg-stone-900">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-stone-200 dark:bg-stone-850 dark:border-stone-700/50 px-8 py-5 flex-shrink-0 flex items-center justify-between">
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
              {/* Unified Trends Chart: completion rate (line) + energy (bar) + env icons */}
              <div className={chartCard}>
                <h3 className={chartTitle}>Completion Rate &amp; Energy</h3>
                <div className="flex items-center gap-4 mb-3">
                  <div className="flex items-center gap-1.5">
                    <div className="w-3 h-0.5 rounded" style={{ backgroundColor: OCEAN }} />
                    <span className="text-xs text-stone-500 dark:text-stone-400">Completion %</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-3 h-3 rounded-sm opacity-70" style={{ backgroundColor: AMBER }} />
                    <span className="text-xs text-stone-500 dark:text-stone-400">Energy (1–5)</span>
                  </div>
                </div>
                {trendsData.length === 0 ? (
                  <div className={`${emptyChart} h-[220px]`}>No data for this period</div>
                ) : (
                  <ResponsiveContainer width="100%" height={260}>
                    <ComposedChart data={trendsData} margin={{ top: 24, right: 16, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                      <XAxis
                        dataKey="date"
                        height={60}
                        interval={xAxisInterval(trendsData.length)}
                        tick={(props) => (
                          <TrendsTick
                            {...props}
                            trendsData={trendsData}
                            tickColor={tickColor}
                          />
                        )}
                      />
                      <YAxis
                        yAxisId="left"
                        domain={[0, 100]}
                        tickFormatter={v => `${v}%`}
                        tick={{ fill: tickColor, fontSize: 11 }}
                      />
                      <YAxis
                        yAxisId="right"
                        orientation="right"
                        domain={[0, 5]}
                        ticks={[1, 2, 3, 4, 5]}
                        tick={{ fill: tickColor, fontSize: 11 }}
                      />
                      <Tooltip
                        content={<TrendsTooltip trendsData={trendsData} isDark={isDark} />}
                      />
                      <Bar
                        yAxisId="right"
                        dataKey="energy"
                        name="Energy"
                        fill={AMBER}
                        opacity={0.7}
                        radius={[3, 3, 0, 0]}
                      />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="completionRate"
                        name="Completion %"
                        stroke={OCEAN}
                        strokeWidth={2}
                        dot={false}
                        connectNulls={false}
                      />
                    </ComposedChart>
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
                    <ComposedChart data={taskVolumeData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                      <XAxis
                        dataKey="date"
                        tick={{ fill: tickColor, fontSize: 11 }}
                        interval={xAxisInterval(taskVolumeData.length)}
                      />
                      <YAxis yAxisId="left" allowDecimals={false} tick={{ fill: tickColor, fontSize: 11 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar yAxisId="left" dataKey="deep_work" name="Deep Work" stackId="a" fill={OCEAN} />
                      <Bar yAxisId="left" dataKey="short_task" name="Short Task" stackId="a" fill={TERRACOTTA} />
                      <Bar yAxisId="left" dataKey="maintenance" name="Maintenance" stackId="a" fill={MOSS} radius={[3, 3, 0, 0]} />
                    </ComposedChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </section>

        </main>
      </div>

      {showExportModal && <ExportModal onClose={() => setShowExportModal(false)} />}
    </div>
  )
}
