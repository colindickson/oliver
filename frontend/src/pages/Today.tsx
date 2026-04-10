import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dayApi, taskApi, backlogApi, templatesApi } from '../api/client'
import type { Task, TaskTemplate } from '../api/client'
import { TaskColumn } from '../components/TaskColumn'
import { Sidebar } from '../components/Sidebar'
import { NotificationBanner } from '../components/NotificationBanner'
import { DayNotes } from '../components/DayNotes'
import { DayRating } from '../components/DayRating'
import { RollForwardModal } from '../components/RollForwardModal'
import { useTheme } from '../contexts/ThemeContext'
import { useMobile } from '../contexts/MobileContext'
import { MobileHeader } from '../components/MobileHeader'
import { BottomTabBar } from '../components/BottomTabBar'
import { MobileTimerStrip } from '../components/MobileTimerStrip'
import { FocusGoalBanner } from '../components/FocusGoalBanner'
import { useTimerDisplay } from '../hooks/useTimerDisplay'
import { CATEGORIES, CATEGORY_LIST, type CategoryKey } from '../constants/categories'

interface ColumnConfig {
  title: string
  category: CategoryKey
  color: CategoryKey
}

const columns: ColumnConfig[] = CATEGORY_LIST.map(c => ({
  title: c.label,
  category: c.key,
  color: c.key,
}))

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
  const isMobile = useMobile()
  const { showTimer } = useTimerDisplay()
  const [activeTab, setActiveTab] = useState<NonNullable<Task['category']>>('deep_work')
  const [rollForwardTask, setRollForwardTask] = useState<Task | null>(null)

  const { data: day, isLoading, isError, refetch } = useQuery({
    queryKey: ['day', 'today'],
    queryFn: dayApi.getToday,
  })

  const createTask = useMutation({
    mutationFn: taskApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['day', 'today'] })
      qc.invalidateQueries({ queryKey: ['goal'] })
      qc.invalidateQueries({ queryKey: ['goals'] })
    },
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
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['day', 'today'] })
      qc.invalidateQueries({ queryKey: ['goal'] })
      qc.invalidateQueries({ queryKey: ['goals'] })
    },
  })

  const deleteTask = useMutation({
    mutationFn: taskApi.delete,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['day', 'today'] })
      qc.invalidateQueries({ queryKey: ['goal'] })
      qc.invalidateQueries({ queryKey: ['goals'] })
    },
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

  const continueTomorrow = useMutation({
    mutationFn: taskApi.continueTomorrow,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['day', 'today'] }),
  })

  const rollForward = useMutation({
    mutationFn: ({ id, targetDate }: { id: number; targetDate: string }) =>
      taskApi.rollForward(id, targetDate),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['day', 'today'] })
      qc.invalidateQueries({ queryKey: ['day'] })
    },
  })

  const scheduleFromBacklog = useMutation({
    mutationFn: ({ taskId, category }: { taskId: number; category: NonNullable<Task['category']> }) => {
      if (!day) throw new Error('Day not loaded')
      return backlogApi.moveToDay(taskId, { day_id: day.id, category })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['day', 'today'] })
      qc.invalidateQueries({ queryKey: ['backlog'] })
    },
  })

  const instantiateTemplate = useMutation({
    mutationFn: ({ template, category }: { template: TaskTemplate; category: NonNullable<Task['category']> }) => {
      if (!day) throw new Error('Day not loaded')
      return templatesApi.instantiate(template.id, day.id, category)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['day', 'today'] }),
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

  function handleContinueTomorrow(task: Task) {
    continueTomorrow.mutate(task.id)
  }

  function handleRollForward(task: Task) {
    setRollForwardTask(task)
  }

  function handleRollForwardConfirm(targetDate: string) {
    if (!rollForwardTask) return
    rollForward.mutate({ id: rollForwardTask.id, targetDate })
    setRollForwardTask(null)
  }

  function handleScheduleFromBacklog(task: Task, category: NonNullable<Task['category']>) {
    scheduleFromBacklog.mutate({ taskId: task.id, category })
  }

  function handleInstantiateFromTemplate(template: TaskTemplate, category: NonNullable<Task['category']>) {
    instantiateTemplate.mutate({ template, category })
  }

  if (isError) {
    if (isMobile) {
      return (
        <div className="flex flex-col h-screen bg-stone-900">
          <MobileHeader title="Today" />
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <p className="text-stone-400 text-sm">Failed to load today's tasks.</p>
            <button onClick={() => void refetch()} className="text-xs text-terracotta-400 hover:text-terracotta-300 underline">
              Retry
            </button>
          </div>
          <BottomTabBar />
        </div>
      )
    }
    return (
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <p className="text-stone-400 text-sm">Failed to load today's tasks.</p>
          <button onClick={() => void refetch()} className="text-xs text-terracotta-400 hover:text-terracotta-300 underline">
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (isLoading || !day) {
    if (isMobile) {
      return (
        <div className="flex flex-col h-screen bg-stone-900">
          <MobileHeader title="Today" />
          <div className="flex-1 flex items-center justify-center text-stone-400 text-sm">
            Loading...
          </div>
          <BottomTabBar />
        </div>
      )
    }
    return (
      <div className="flex h-screen overflow-hidden">
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

  // Mobile layout
  if (isMobile) {
    const activeColumn = columns.find(c => c.category === activeTab)!
    return (
      <div className="flex flex-col h-screen bg-stone-900">
        <MobileHeader title="Today" />

        {/* Date + progress */}
        <div className="px-4 py-3 flex items-center justify-between border-b border-stone-700/50 flex-shrink-0">
          <p className="text-sm text-stone-400">{formatDate(new Date())}</p>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-stone-200 tabular-nums">
              {completedTasks}<span className="text-stone-500">/{totalTasks}</span>
            </span>
            <div className="relative w-8 h-8">
              <svg className="w-8 h-8 -rotate-90" viewBox="0 0 48 48">
                <circle cx="24" cy="24" r="20" fill="none" stroke="#44403c" strokeWidth="5" />
                <circle
                  cx="24" cy="24" r="20" fill="none"
                  stroke={progressPct === 100 ? '#4a8a4a' : '#e86b3a'}
                  strokeWidth="5" strokeLinecap="round"
                  strokeDasharray={`${progressPct * 1.256} 125.6`}
                  className="transition-all duration-500"
                />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-[9px] font-medium text-stone-300">
                {progressPct}%
              </span>
            </div>
          </div>
        </div>

        {/* Focus Goal Banner */}
        <FocusGoalBanner />

        {/* Tab strip */}
        <div className="flex border-b border-stone-700/50 flex-shrink-0">
          {columns.map(col => (
            <button
              key={col.category}
              onClick={() => setActiveTab(col.category)}
              className={`flex-1 py-2.5 text-xs font-semibold transition-colors ${
                activeTab === col.category
                  ? CATEGORIES[col.color].tab
                  : 'text-stone-500'
              }`}
            >
              {col.title}
            </button>
          ))}
        </div>

        {/* Active column — scrollable */}
        <div className="flex-1 overflow-y-auto px-4 py-4 pb-[120px]">
          <TaskColumn
            title={activeColumn.title}
            category={activeColumn.category}
            tasks={day.tasks}
            colorClass={activeColumn.color}
            onAddTask={(title, desc, tags) => handleAddTask(activeColumn.category, title, desc, tags)}
            onComplete={handleComplete}
            onDelete={handleDelete}
            onReorder={handleReorder}
            onMoveToBacklog={handleMoveToBacklog}
            onContinueTomorrow={handleContinueTomorrow}
            onRollForward={handleRollForward}
            onScheduleFromBacklog={(task) => handleScheduleFromBacklog(task, activeColumn.category)}
            onInstantiateFromTemplate={(template) => handleInstantiateFromTemplate(template, activeColumn.category)}
          />

          {/* Notes + Rating always below tabs */}
          <div className="mt-8 space-y-6">
            <DayNotes
              label="Notes"
              dayId={day.id}
              initialContent={day.notes?.content ?? ''}
              onSave={(dayId, content) => upsertNotes.mutateAsync({ dayId, content })}
            />
            <DayNotes
              label="Roadblocks"
              dayId={day.id}
              initialContent={day.roadblocks?.content ?? ''}
              onSave={(dayId, content) => upsertRoadblocks.mutateAsync({ dayId, content })}
            />
            <DayRating
              dayId={day.id}
              initialRating={day.rating}
              onSave={(dayId, rating) => upsertRating.mutateAsync({ dayId, rating })}
            />
          </div>
        </div>

        {showTimer && <MobileTimerStrip />}
        <BottomTabBar />
        <NotificationBanner />
        {rollForwardTask && (
          <RollForwardModal
            onConfirm={handleRollForwardConfirm}
            onCancel={() => setRollForwardTask(null)}
          />
        )}
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-stone-25 dark:bg-stone-900">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-stone-200 px-8 py-5 flex items-center justify-between flex-shrink-0 dark:bg-stone-850 dark:border-stone-700/50">
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

        {/* Focus Goal Banner */}
        <FocusGoalBanner />

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
                onContinueTomorrow={handleContinueTomorrow}
                onRollForward={handleRollForward}
                onScheduleFromBacklog={(task) => handleScheduleFromBacklog(task, col.category)}
                onInstantiateFromTemplate={(template) => handleInstantiateFromTemplate(template, col.category)}
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

      {rollForwardTask && (
        <RollForwardModal
          onConfirm={handleRollForwardConfirm}
          onCancel={() => setRollForwardTask(null)}
        />
      )}
    </div>
  )
}
