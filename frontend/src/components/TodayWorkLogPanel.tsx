import { useQuery } from '@tanstack/react-query'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { workLogApi } from '../api/client'
import type { WorkLog } from '../api/client'
import { useTheme } from '../contexts/ThemeContext'
import { toLocalDateStr } from '../utils/format'

const TAG_COLORS: Record<string, string> = {
  commit:   '#5b5bd6',
  pr:       '#e86b3a',
  review:   '#4a8a4a',
  research: '#d97706',
  untyped:  '#a8a29e',
}

const TAG_BG: Record<string, string> = {
  commit:   '#ede9fe',
  pr:       '#ffedd5',
  review:   '#dcfce7',
  research: '#fef3c7',
  untyped:  '#f5f5f4',
}

const TAG_TEXT: Record<string, string> = {
  commit:   '#5b5bd6',
  pr:       '#e86b3a',
  review:   '#4a8a4a',
  research: '#d97706',
  untyped:  '#78716c',
}

const TAG_ORDER = ['commit', 'pr', 'review', 'research', 'untyped']

function buildChartData(logs: WorkLog[]) {
  const counts: Record<string, number> = {}
  for (const log of logs) {
    const tags = log.tags.length > 0 ? log.tags : ['untyped']
    for (const tag of tags) {
      const key = TAG_ORDER.includes(tag) ? tag : 'untyped'
      counts[key] = (counts[key] ?? 0) + 1
    }
  }
  return TAG_ORDER
    .filter(t => counts[t] > 0)
    .map(t => ({ name: t, value: counts[t] }))
}

export function TodayWorkLogPanel() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const todayStr = toLocalDateStr(new Date())

  const { data: logs = [] } = useQuery({
    queryKey: ['work-logs', todayStr],
    queryFn: () => workLogApi.listByDate(todayStr),
  })

  const chartData = buildChartData(logs)
  const total = logs.length

  const bg        = isDark ? 'bg-stone-800/80'            : 'bg-white'
  const border    = isDark ? 'border-stone-700'           : 'border-stone-100'
  const heading   = isDark ? 'text-stone-400'             : 'text-stone-400'
  const divider   = isDark ? 'border-stone-700'           : 'border-stone-100'
  const rowBorder = isDark ? 'border-stone-700/60'        : 'border-stone-50'
  const projText  = isDark ? 'text-stone-200'             : 'text-stone-700'
  const descText  = isDark ? 'text-stone-400'             : 'text-stone-500'
  const thText    = isDark ? 'text-stone-500'             : 'text-stone-400'
  const emptyText = isDark ? 'text-stone-500'             : 'text-stone-400'
  const legendTxt = isDark ? 'text-stone-300'             : 'text-stone-600'
  const countTxt  = isDark ? 'text-stone-100'             : 'text-stone-800'
  const countSub  = isDark ? 'text-stone-500'             : 'text-stone-400'

  return (
    <div className={`${bg} rounded-xl border ${border} p-5`}>
      <p className={`text-[10px] font-semibold tracking-widest uppercase mb-4 ${heading}`}>
        Work Log
      </p>

      {total === 0 ? (
        <p className={`text-sm ${emptyText} text-center py-6`}>No work logged yet</p>
      ) : (
        <div className="flex gap-6 items-start">
          {/* Donut chart + legend */}
          <div className="flex flex-col items-center gap-3 shrink-0">
            <div className="relative w-[100px] h-[100px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={30}
                    outerRadius={46}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {chartData.map((entry) => (
                      <Cell key={entry.name} fill={TAG_COLORS[entry.name] ?? TAG_COLORS.untyped} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number, name: string) => [value, name]}
                    contentStyle={{
                      background: isDark ? '#2a2520' : '#ffffff',
                      border: `1px solid ${isDark ? '#3d3830' : '#e5e1db'}`,
                      borderRadius: 6,
                      fontSize: 11,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              {/* Centre label */}
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className={`text-lg font-bold leading-none ${countTxt}`}>{total}</span>
                <span className={`text-[9px] ${countSub}`}>entries</span>
              </div>
            </div>

            {/* Legend */}
            <div className="flex flex-col gap-1">
              {chartData.map((entry) => {
                const pct = Math.round((entry.value / total) * 100)
                return (
                  <div key={entry.name} className="flex items-center gap-1.5">
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ background: TAG_COLORS[entry.name] ?? TAG_COLORS.untyped }}
                    />
                    <span className={`text-[10px] ${legendTxt}`}>
                      {entry.name} <strong>{pct}%</strong>
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Vertical divider */}
          <div className={`w-px self-stretch border-l ${divider}`} />

          {/* Entry table */}
          <div className="flex-1 max-h-[160px] overflow-y-auto">
            <table className="w-full border-collapse text-[11px]">
              <thead className={`sticky top-0 ${bg}`}>
                <tr className={`border-b ${rowBorder}`}>
                  <th className={`text-left pb-2 pr-3 font-semibold tracking-wider text-[10px] uppercase ${thText}`}>Project</th>
                  <th className={`text-left pb-2 pr-3 font-semibold tracking-wider text-[10px] uppercase ${thText}`}>Description</th>
                  <th className={`text-left pb-2 font-semibold tracking-wider text-[10px] uppercase ${thText}`}>Tags</th>
                </tr>
              </thead>
              <tbody>
                {[...logs]
                  .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                  .map((log) => (
                    <tr key={log.id} className={`border-b ${rowBorder} last:border-0`}>
                      <td className={`py-1.5 pr-3 font-medium ${projText} whitespace-nowrap`}>
                        {log.project_name}
                      </td>
                      <td className={`py-1.5 pr-3 ${descText}`}>{log.description}</td>
                      <td className="py-1.5">
                        <div className="flex flex-wrap gap-1">
                          {(log.tags.length > 0 ? log.tags : ['untyped']).map((tag) => (
                            <span
                              key={tag}
                              className="rounded px-1.5 py-0.5 text-[9px] font-medium"
                              style={{
                                background: TAG_BG[tag] ?? TAG_BG.untyped,
                                color: TAG_TEXT[tag] ?? TAG_TEXT.untyped,
                              }}
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
