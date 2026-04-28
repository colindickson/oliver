import { useQuery } from '@tanstack/react-query'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  type TooltipProps as RechartsTooltipProps,
} from 'recharts'
import { analyticsApi } from '../api/client'
import type { ValueType, NameType } from 'recharts/types/component/DefaultTooltipContent'

const COMMIT_COLOR = '#5b5bd6'
const PR_COLOR = '#e86b3a'
const REVIEW_COLOR = '#4a8a4a'
const RESEARCH_COLOR = '#d97706'
const UNTYPED_COLOR = '#a8a29e'

function formatChartDate(dateStr: string): string {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

type CustomTooltipProps = RechartsTooltipProps<ValueType, NameType> & { isDark: boolean }

function CustomTooltip({ active, payload, label, isDark }: CustomTooltipProps) {
  if (!active || !payload?.length) return null
  const total = payload.reduce((s, p) => s + (Number(p.value) || 0), 0)
  const bg = isDark ? '#2a2520' : '#ffffff'
  const border = isDark ? '#3d3830' : '#e5e1db'
  const text = isDark ? '#e8e0d8' : '#1a1714'
  const muted = isDark ? '#8a847d' : '#5c5750'

  return (
    <div style={{ background: bg, border: `1px solid ${border}`, borderRadius: 6, padding: '8px 12px', fontSize: 12 }}>
      <div style={{ color: muted, marginBottom: 6 }}>{label ? formatChartDate(label) : ''}</div>
      {payload.filter(p => Number(p.value) > 0).map(p => (
        <div key={String(p.name)} style={{ display: 'flex', justifyContent: 'space-between', gap: 16, color: text }}>
          <span style={{ color: p.color }}>{String(p.name)}</span>
          <span>{Number(p.value)}</span>
        </div>
      ))}
      <div style={{ borderTop: `1px solid ${border}`, marginTop: 4, paddingTop: 4, display: 'flex', justifyContent: 'space-between', gap: 16, color: muted }}>
        <span>total</span>
        <span>{total}</span>
      </div>
    </div>
  )
}

interface Props {
  days: number
  isDark: boolean
}

export function WorkLogActivityChart({ days, isDark }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ['workLogActivity', days],
    queryFn: () => analyticsApi.getWorkLogActivity(days),
  })

  const axisColor = isDark ? '#5c5750' : '#a8a29e'
  const gridColor = isDark ? '#2a2520' : '#f0ece8'

  if (isLoading) {
    return <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: axisColor, fontSize: 13 }}>Loading…</div>
  }

  if (!data || data.length === 0) {
    return <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: axisColor, fontSize: 13 }}>No work logs in this period</div>
  }

  const interval = Math.max(0, Math.floor(data.length / 8) - 1)

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }} barSize={data.length > 30 ? 6 : 12}>
        <XAxis
          dataKey="date"
          tickFormatter={formatChartDate}
          interval={interval}
          tick={{ fontSize: 11, fill: axisColor }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fontSize: 11, fill: axisColor }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={(props) => <CustomTooltip {...props} isDark={isDark} />} />
        <Legend iconType="square" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
        <Bar dataKey="commit" name="commit" stackId="a" fill={COMMIT_COLOR} />
        <Bar dataKey="pr" name="pr" stackId="a" fill={PR_COLOR} />
        <Bar dataKey="review" name="review" stackId="a" fill={REVIEW_COLOR} />
        <Bar dataKey="research" name="research" stackId="a" fill={RESEARCH_COLOR} />
        <Bar dataKey="untyped" name="untyped" stackId="a" fill={UNTYPED_COLOR} radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
