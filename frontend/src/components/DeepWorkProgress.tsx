import { useQuery } from '@tanstack/react-query'
import { analyticsApi, dayApi, timerApi } from '../api/client'

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------

function formatProgressTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) {
    return `${h}h ${m}m`
  }
  return `${m}m`
}

// -----------------------------------------------------------------------------
// DeepWorkProgress
// -----------------------------------------------------------------------------

interface DeepWorkProgressProps {
  className?: string
}

export function DeepWorkProgress({ className = '' }: DeepWorkProgressProps) {
  const { data: deepWorkData } = useQuery({
    queryKey: ['analytics', 'today-deep-work'],
    queryFn: analyticsApi.getTodayDeepWork,
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  const { data: timer } = useQuery({
    queryKey: ['timer', 'current'],
    queryFn: timerApi.getCurrent,
    refetchInterval: 1000,
  })

  const { data: day } = useQuery({
    queryKey: ['day', 'today'],
    queryFn: dayApi.getToday,
  })

  const totalSeconds = deepWorkData?.total_seconds ?? 0
  const goalSeconds = deepWorkData?.goal_seconds ?? 10800

  // Check if timer is running on a deep work task
  const isTimerRunning = timer?.status === 'running'
  const timerTaskId = timer?.task_id
  const timerTask = timerTaskId ? day?.tasks.find(t => t.id === timerTaskId) : null
  const isDeepWorkTask = timerTask?.category === 'deep_work'

  // Add current elapsed time if timer is running on a deep work task
  const elapsedSeconds = isTimerRunning && isDeepWorkTask ? (timer?.elapsed_seconds ?? 0) : 0
  const displaySeconds = totalSeconds + elapsedSeconds

  // Calculate progress percentage (capped at 100)
  const progressPercent = Math.min((displaySeconds / goalSeconds) * 100, 100)
  const isComplete = progressPercent >= 100

  return (
    <div className={`${className}`}>
      {/* Progress bar */}
      <div className="relative h-1.5 bg-stone-700/50 rounded-full overflow-hidden">
        {/* Progress fill */}
        <div
          className={`absolute inset-y-0 left-0 rounded-full transition-all duration-300 ${
            isComplete
              ? 'bg-gradient-to-r from-moss-500 to-moss-400'
              : 'bg-gradient-to-r from-terracotta-600 to-terracotta-400'
          } ${isTimerRunning && isDeepWorkTask ? 'animate-progress-glow' : ''}`}
          style={{ width: `${progressPercent}%` }}
        />

        {/* Segment dividers (visual echo of 3-3-3) */}
        <div className="absolute inset-0 flex">
          <div className="flex-1 border-r border-stone-600/30" />
          <div className="flex-1 border-r border-stone-600/30" />
          <div className="flex-1" />
        </div>
      </div>

      {/* Progress text */}
      <div className="flex justify-between items-center mt-1.5">
        <span className="text-[10px] text-stone-500 font-mono">
          {formatProgressTime(displaySeconds)} toward 3h goal
        </span>
        <span className={`text-[10px] font-mono ${isComplete ? 'text-moss-400' : 'text-stone-500'}`}>
          {Math.round(progressPercent)}%
        </span>
      </div>
    </div>
  )
}
