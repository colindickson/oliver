import { useQuery } from '@tanstack/react-query'
import { timerApi } from '../api/client'

function formatDuration(seconds: number | null): string {
  if (seconds == null) return '\u2014'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m >= 60) {
    const h = Math.floor(m / 60)
    return `${h}h ${m % 60}m`
  }
  return `${m}m ${s}s`
}

interface Props {
  taskId: number
}

export function SessionHistory({ taskId }: Props) {
  const { data: sessions = [] } = useQuery({
    queryKey: ['sessions', taskId],
    queryFn: () => timerApi.getSessions(taskId),
  })

  if (sessions.length === 0) return null

  return (
    <div className="mt-2">
      <p className="text-xs text-gray-400 font-medium mb-1">Sessions</p>
      <div className="space-y-0.5">
        {sessions.map(s => (
          <div key={s.id} className="flex items-center justify-between text-xs text-gray-500">
            <span>{new Date(s.started_at).toLocaleTimeString()}</span>
            <span className="font-mono">{formatDuration(s.duration_seconds)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
