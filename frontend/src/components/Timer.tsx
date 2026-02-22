import { useTimer } from '../hooks/useTimer'

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

interface Props {
  activeTaskId?: number
}

export function Timer({ activeTaskId }: Props) {
  const { timer, startTimer, pauseTimer, stopTimer } = useTimer()

  const status = timer?.status ?? 'idle'
  const elapsed = timer?.elapsed_seconds ?? 0

  const isRunning = status === 'running'
  const isPaused = status === 'paused'
  const isIdle = status === 'idle'

  function handleStart() {
    const taskId = activeTaskId ?? timer?.task_id
    if (!taskId) return
    startTimer.mutate(taskId)
  }

  return (
    <div className="flex items-center gap-3 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2">
      {/* Time display */}
      <span
        className={`font-mono text-lg font-semibold tabular-nums ${
          isRunning ? 'text-blue-600' : isPaused ? 'text-amber-600' : 'text-slate-400'
        }`}
      >
        {formatTime(elapsed)}
      </span>

      {/* Controls */}
      <div className="flex items-center gap-1">
        {(isIdle || isPaused) && (
          <button
            type="button"
            onClick={handleStart}
            disabled={isIdle && !activeTaskId && !timer?.task_id}
            className="text-xs bg-blue-600 text-white rounded px-3 py-1 hover:bg-blue-700 disabled:opacity-40"
          >
            {isPaused ? 'Resume' : 'Start'}
          </button>
        )}
        {isRunning && (
          <button
            type="button"
            onClick={() => pauseTimer.mutate()}
            className="text-xs bg-amber-500 text-white rounded px-3 py-1 hover:bg-amber-600"
          >
            Pause
          </button>
        )}
        {!isIdle && (
          <button
            type="button"
            onClick={() => stopTimer.mutate()}
            className="text-xs bg-slate-600 text-white rounded px-3 py-1 hover:bg-slate-700"
          >
            Stop
          </button>
        )}
      </div>

      {/* Status label */}
      <span className="text-xs text-slate-400 capitalize">{status}</span>
    </div>
  )
}
