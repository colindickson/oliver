import { useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { timerApi, dayApi } from '../api/client'
import { DeepWorkProgress } from './DeepWorkProgress'

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

// -----------------------------------------------------------------------------
// SidebarTimer
// -----------------------------------------------------------------------------

export function SidebarTimer() {
  const qc = useQueryClient()

  const { data: timer } = useQuery({
    queryKey: ['timer', 'current'],
    queryFn: timerApi.getCurrent,
    refetchInterval: 1000,
    refetchIntervalInBackground: false,
  })

  const { data: day } = useQuery({
    queryKey: ['day', 'today'],
    queryFn: dayApi.getToday,
  })

  const startTimer = useMutation({
    mutationFn: timerApi.start,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['timer'] }),
  })

  const pauseTimer = useMutation({
    mutationFn: timerApi.pause,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['timer'] }),
  })

  const stopTimer = useMutation({
    mutationFn: timerApi.stop,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['timer'] })
      qc.invalidateQueries({ queryKey: ['sessions'] })
    },
  })

  const status = timer?.status ?? 'idle'
  const elapsed = timer?.elapsed_seconds ?? 0

  const isRunning = status === 'running'
  const isPaused = status === 'paused'
  const isIdle = status === 'idle'

  // Find the first incomplete deep work task
  const activeTask = day?.tasks.find(
    t => t.category === 'deep_work' && t.status !== 'completed'
  )

  function handleStart() {
    const taskId = activeTask?.id ?? timer?.task_id
    if (!taskId) return
    startTimer.mutate(taskId)
  }

  function handleToggle() {
    if (isRunning) {
      pauseTimer.mutate()
    } else {
      handleStart()
    }
  }

  // Keyboard shortcut: 'T' toggles timer
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return
      }
      if (e.key === 't' || e.key === 'T') {
        handleToggle()
      }
    }

    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [isRunning, activeTask, timer?.task_id])

  // Find task name if timer is active
  const activeTaskName = timer?.task_id
    ? day?.tasks.find(t => t.id === timer.task_id)?.title
    : activeTask?.title

  return (
    <div className="p-4 border-t border-stone-700/50 bg-stone-900/50 dark:bg-stone-900/70">
      {/* Timer display */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {/* Status indicator */}
          <div
            className={`w-2 h-2 rounded-full ${
              isRunning
                ? 'bg-terracotta-500 animate-pulse'
                : isPaused
                  ? 'bg-amber-400'
                  : 'bg-stone-600'
            }`}
          />
          <span
            className={`font-mono text-xl font-semibold tabular-nums ${
              isRunning
                ? 'text-terracotta-400'
                : isPaused
                  ? 'text-amber-400'
                  : 'text-stone-400'
            }`}
          >
            {formatTime(elapsed)}
          </span>
        </div>

        {/* Status label */}
        <span className="text-[10px] uppercase tracking-wider text-stone-500">
          {status}
        </span>
      </div>

      {/* Task name */}
      {activeTaskName && (
        <p className="text-xs text-stone-400 truncate mb-3">
          {activeTaskName}
        </p>
      )}

      {/* Deep work progress */}
      <DeepWorkProgress className="mb-3" />

      {/* Controls */}
      <div className="flex gap-2">
        {(isIdle || isPaused) && (
          <button
            type="button"
            onClick={handleStart}
            disabled={isIdle && !activeTask && !timer?.task_id}
            className={`
              flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-200
              ${isIdle && !activeTask && !timer?.task_id
                ? 'bg-stone-700 text-stone-500 cursor-not-allowed'
                : 'bg-terracotta-600 text-white hover:bg-terracotta-500 active:scale-[0.98]'}
              ${isRunning ? 'timer-running' : ''}
            `}
          >
            {isPaused ? 'Resume' : 'Start Focus'}
          </button>
        )}

        {isRunning && (
          <button
            type="button"
            onClick={() => pauseTimer.mutate()}
            className="flex-1 py-2 rounded-lg text-sm font-medium bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 transition-colors"
          >
            Pause
          </button>
        )}

        {!isIdle && (
          <button
            type="button"
            onClick={() => stopTimer.mutate()}
            className="py-2 px-4 rounded-lg text-sm font-medium bg-stone-700 text-stone-300 hover:bg-stone-600 transition-colors"
          >
            Stop
          </button>
        )}
      </div>

      {/* Keyboard hint */}
      <p className="text-[10px] text-stone-600 text-center mt-2">
        Press <kbd className="px-1 py-0.5 bg-stone-700 rounded text-stone-400">T</kbd> to toggle timer
      </p>
    </div>
  )
}
