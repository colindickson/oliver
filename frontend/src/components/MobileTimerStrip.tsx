import { useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { timerApi, dayApi } from '../api/client'

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export function MobileTimerStrip() {
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

  const handleToggleRef = useRef(handleToggle)
  handleToggleRef.current = handleToggle

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (e.key === 't' || e.key === 'T') handleToggleRef.current()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [])

  const activeTaskName = timer?.task_id
    ? day?.tasks.find(t => t.id === timer.task_id)?.title
    : activeTask?.title

  return (
    <div className="fixed bottom-[56px] left-0 right-0 z-40 bg-stone-900/95 backdrop-blur-sm border-t border-stone-700/50 px-4 py-2 flex items-center gap-3">
      {/* Status dot */}
      <div
        className={`w-2 h-2 rounded-full flex-shrink-0 ${
          isRunning ? 'bg-terracotta-500 animate-pulse' : isPaused ? 'bg-amber-400' : 'bg-stone-600'
        }`}
      />

      {/* Time */}
      <span
        className={`font-mono text-base font-semibold tabular-nums flex-shrink-0 ${
          isRunning ? 'text-terracotta-400' : isPaused ? 'text-amber-400' : 'text-stone-500'
        }`}
      >
        {formatTime(elapsed)}
      </span>

      {/* Task name */}
      <span className="flex-1 text-xs text-stone-400 truncate min-w-0">
        {activeTaskName ?? 'No active task'}
      </span>

      {/* Controls */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {(isIdle || isPaused) && (
          <button
            type="button"
            onClick={handleStart}
            disabled={isIdle && !activeTask && !timer?.task_id}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
              isIdle && !activeTask && !timer?.task_id
                ? 'bg-stone-700 text-stone-500 cursor-not-allowed'
                : 'bg-terracotta-600 text-white hover:bg-terracotta-500'
            }`}
          >
            {isPaused ? 'Resume' : 'Start'}
          </button>
        )}

        {isRunning && (
          <button
            type="button"
            onClick={() => pauseTimer.mutate()}
            className="px-3 py-1 rounded-lg text-xs font-medium bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 transition-colors"
          >
            Pause
          </button>
        )}

        {!isIdle && (
          <button
            type="button"
            onClick={() => stopTimer.mutate()}
            className="px-3 py-1 rounded-lg text-xs font-medium bg-stone-700 text-stone-300 hover:bg-stone-600 transition-colors"
          >
            Stop
          </button>
        )}
      </div>
    </div>
  )
}
