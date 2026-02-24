import { useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dayApi, taskApi, backlogApi } from '../api/client'
import type { Task } from '../api/client'
import { TaskColumn } from '../components/TaskColumn'
import { Sidebar } from '../components/Sidebar'
import { NotificationBanner } from '../components/NotificationBanner'
import { DayNotes } from '../components/DayNotes'
import { DayRating } from '../components/DayRating'
import { useTheme } from '../contexts/ThemeContext'

interface ColumnConfig {
  title: string
  category: NonNullable<Task['category']>
  color: 'blue' | 'amber' | 'green'
}

const columns: ColumnConfig[] = [
  { title: 'Deep Work', category: 'deep_work', color: 'blue' },
  { title: 'Short Tasks', category: 'short_task', color: 'amber' },
  { title: 'Maintenance', category: 'maintenance', color: 'green' },
]

function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  })
}

export function Today() {
  const qc = useQueryClient()
  const { theme } = useTheme()

  const { data: day, isLoading } = useQuery({
    queryKey: ['day', 'today'],
    queryFn: dayApi.getToday,
  })

  const createTask = useMutation({
    mutationFn: taskApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['day', 'today'] }),
  })

  const upsertNotes = useMutation({
    mutationFn: ({ dayId, content }: { dayId: number; content: string }) =>
      dayApi.upsertNotes(dayId, content),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['day', 'today'] }),
  })

  const upsertRoadblocks = useMutation({
    mutationFn: ({ dayId, content }: { dayId: number; content: string }) =>
      dayApi.upsertRoadblocks(dayId, content),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['day', 'today'] }),
  })

  const upsertRating = useMutation({
    mutationFn: ({ dayId, rating }: { dayId: number; rating: Parameters<typeof dayApi.upsertRating>[1] }) =>
      dayApi.upsertRating(dayId, rating),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['day', 'today'] }),
  })

  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: Task['status'] }) =>
      taskApi.setStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['day', 'today'] }),
  })

  const deleteTask = useMutation({
    mutationFn: taskApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['day', 'today'] }),
  })

  const reorderTasks = useMutation({
    mutationFn: taskApi.reorder,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['day', 'today'] }),
  })

  const moveToBacklog = useMutation({
    mutationFn: taskApi.moveToBacklog,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['day', 'today'] })
      qc.invalidateQueries({ queryKey: ['backlog'] })
    },
  })

  const scheduleFromBacklog = useMutation({
    mutationFn: ({ taskId, category }: { taskId: number; category: NonNullable<Task['category']> }) =>
      backlogApi.moveToDay(taskId, { day_id: day!.id, category }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['day', 'today'] })
      qc.invalidateQueries({ queryKey: ['backlog'] })
    },
  })

  // Keyboard shortcut: 'n' opens the first column's Add task form
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return
      }
      if (e.key === 'n') {
        document.querySelector<HTMLButtonElement>('button[data-add-task]')?.click()
      }
    }

    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [])

  async function handleAddTask(
    category: Task['category'],
    title: string,
    description: string,
    tags: string[],
  ) {
    if (!day) return
    await createTask.mutateAsync({
      day_id: day.id,
      category,
      title,
      description: description || undefined,
      tags: tags.length > 0 ? tags : undefined,
    })
  }

  function handleComplete(task: Task) {
    const next: Task['status'] = task.status === 'completed' ? 'pending' : 'completed'
    setStatus.mutate({ id: task.id, status: next })
  }

  function handleDelete(id: number) {
    deleteTask.mutate(id)
  }

  function handleReorder(taskIds: number[]) {
    reorderTasks.mutate(taskIds)
  }

  function handleMoveToBacklog(task: Task) {
    moveToBacklog.mutate(task.id)
  }

  function handleScheduleFromBacklog(task: Task, category: NonNullable<Task['category']>) {
    scheduleFromBacklog.mutate({ taskId: task.id, category })
  }

  if (isLoading || !day) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center text-stone-400 text-sm">
          Loading...
        </div>
      </div>
    )
  }

  // Calculate progress
  const totalTasks = day.tasks.length
  const completedTasks = day.tasks.filter(t => t.status === 'completed').length
  const progressPct = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0

  return (
    <div className="flex min-h-screen bg-stone-25 dark:bg-stone-800">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-stone-200 px-8 py-5 flex items-center justify-between flex-shrink-0 dark:bg-stone-800/90 dark:border-stone-700/50">
          <div>
            <h1 className="text-xl font-semibold text-stone-800 dark:text-stone-100">Today</h1>
            <p className="text-sm text-stone-400 mt-0.5">{formatDate(new Date())}</p>
          </div>

          {/* Progress indicator */}
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-2xl font-semibold text-stone-800 dark:text-stone-100 tabular-nums">
                {completedTasks}<span className="text-stone-400">/{totalTasks}</span>
              </p>
              <p className="text-xs text-stone-400">tasks completed</p>
            </div>

            {/* Progress ring */}
            <div className="relative w-12 h-12">
              <svg className="w-12 h-12 -rotate-90" viewBox="0 0 48 48">
                <circle
                  cx="24"
                  cy="24"
                  r="20"
                  fill="none"
                  stroke={theme === 'dark' ? '#44403c' : '#e7e5e4'}
                  strokeWidth="4"
                />
                <circle
                  cx="24"
                  cy="24"
                  r="20"
                  fill="none"
                  stroke={progressPct === 100 ? '#4a8a4a' : '#e86b3a'}
                  strokeWidth="4"
                  strokeLinecap="round"
                  strokeDasharray={`${progressPct * 1.256} 125.6`}
                  className="transition-all duration-500"
                />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-stone-600 dark:text-stone-300">
                {progressPct}%
              </span>
            </div>
          </div>
        </header>

        {/* Three-column board */}
        <main className="flex-1 p-8 overflow-auto">
          <div className="flex gap-6 mb-8">
            {columns.map(col => (
              <TaskColumn
                key={col.category}
                title={col.title}
                category={col.category}
                tasks={day.tasks}
                colorClass={col.color}
                onAddTask={(title, desc, tags) => handleAddTask(col.category, title, desc, tags)}
                onComplete={handleComplete}
                onDelete={handleDelete}
                onReorder={handleReorder}
                onMoveToBacklog={handleMoveToBacklog}
                onScheduleFromBacklog={(task) => handleScheduleFromBacklog(task, col.category)}
              />
            ))}
          </div>

          {/* Notes, Roadblocks, and Rating */}
          <div className="max-w-2xl space-y-6">
            <DayNotes
              label="Notes"
              dayId={day.id}
              initialContent={day.notes?.content ?? ''}
              onSave={(dayId, content) =>
                upsertNotes.mutateAsync({ dayId, content })
              }
            />
            <DayNotes
              label="Roadblocks"
              dayId={day.id}
              initialContent={day.roadblocks?.content ?? ''}
              onSave={(dayId, content) =>
                upsertRoadblocks.mutateAsync({ dayId, content })
              }
            />
            <DayRating
              dayId={day.id}
              initialRating={day.rating}
              onSave={(dayId, rating) =>
                upsertRating.mutateAsync({ dayId, rating })
              }
            />
          </div>
        </main>
      </div>

      {/* Notification banner */}
      <NotificationBanner />
    </div>
  )
}
