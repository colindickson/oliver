import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/client'
import type { WorkLogActivityDay } from '../api/client'

interface Props {
  days?: number
  isDark: boolean
}

const INDIGO = '#5b5bd6'

function getCellColor(count: number, isDark: boolean): string {
  if (count === 0) return isDark ? '#292524' : '#f5f5f4'
  if (count === 1) return isDark ? 'rgba(91,91,214,0.25)' : 'rgba(91,91,214,0.2)'
  if (count === 2) return isDark ? 'rgba(91,91,214,0.5)' : 'rgba(91,91,214,0.45)'
  if (count === 3) return isDark ? 'rgba(91,91,214,0.75)' : 'rgba(91,91,214,0.7)'
  return INDIGO
}

export function WorkLogActivityMap({ days = 84, isDark }: Props) {
  const { data: activityData = [] } = useQuery({
    queryKey: ['analytics', 'work-log-activity', days],
    queryFn: () => analyticsApi.getWorkLogActivity(days),
  })

  const activityMap = new Map<string, WorkLogActivityDay>()
  for (const d of activityData) activityMap.set(d.date, d)

  // Build grid ending today
  const today = new Date()
  const grid: { date: string; count: number; projects: string[] }[] = []
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const dateStr = d.toISOString().slice(0, 10)
    const activity = activityMap.get(dateStr)
    grid.push({ date: dateStr, count: activity?.count ?? 0, projects: activity?.projects ?? [] })
  }

  // Chunk into columns of 7 days
  const weeks: typeof grid[] = []
  for (let i = 0; i < grid.length; i += 7) {
    weeks.push(grid.slice(i, i + 7))
  }

  return (
    <div style={{ display: 'flex', gap: 3 }}>
      {weeks.map((week, wi) => (
        <div key={wi} style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {week.map(cell => (
            <div
              key={cell.date}
              title={
                cell.count === 0
                  ? cell.date
                  : `${cell.date}: ${cell.count} log${cell.count !== 1 ? 's' : ''} — ${cell.projects.join(', ')}`
              }
              style={{
                width: 12,
                height: 12,
                borderRadius: 2,
                backgroundColor: getCellColor(cell.count, isDark),
              }}
            />
          ))}
        </div>
      ))}
      {/* Legend */}
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 3, paddingBottom: 1, marginLeft: 6 }}>
        <span style={{ fontSize: 10, color: isDark ? '#78716c' : '#a8a29e' }}>Less</span>
        {[0, 1, 2, 3, 4].map(n => (
          <div
            key={n}
            style={{ width: 12, height: 12, borderRadius: 2, backgroundColor: getCellColor(n, isDark) }}
          />
        ))}
        <span style={{ fontSize: 10, color: isDark ? '#78716c' : '#a8a29e' }}>More</span>
      </div>
    </div>
  )
}
