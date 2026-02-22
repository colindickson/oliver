import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dayApi, taskApi } from '../api/client'
import type { Task } from '../api/client'
import { Sidebar } from '../components/Sidebar'

interface AddTaskFormProps {
  category: 'deep_work' | 'short_task' | 'maintenance'
  isOpen: boolean
  title: string
  onOpen: () => void
  onTitleChange: (value: string) => void
  onSubmit: () => void
  onCancel: () => void
  mt?: boolean
}

function AddTaskForm({ category, isOpen, title, onOpen, onTitleChange, onSubmit, onCancel, mt }: AddTaskFormProps) {
  if (isOpen) {
    return (
      <form
        onSubmit={e => { e.preventDefault(); onSubmit() }}
        className={`flex items-center gap-2${mt ? ' mt-2' : ''}`}
      >
        <input
          autoFocus
          value={title}
          onChange={e => onTitleChange(e.target.value)}
          onKeyDown={e => { if (e.key === 'Escape') onCancel() }}
          placeholder="Task title…"
          className="flex-1 text-sm px-3 py-2 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-terracotta-300 bg-white"
        />
        <button
          type="submit"
          disabled={!title.trim()}
          className="px-3 py-2 text-sm font-medium text-white bg-terracotta-500 rounded-xl hover:bg-terracotta-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Add
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-2 text-sm text-stone-400 hover:text-stone-600 transition-colors"
        >
          Cancel
        </button>
      </form>
    )
  }
  return (
    <button
      onClick={onOpen}
      className={`${mt ? 'mt-2 ' : ''}w-full text-left text-xs text-stone-400 hover:text-stone-600 flex items-center gap-1.5 px-1 py-1 rounded-lg hover:bg-white/60 transition-colors`}
    >
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M6 2v8M2 6h8" strokeLinecap="round" />
      </svg>
      Add task
    </button>
  )
}

const categories = [
  { key: 'deep_work', label: 'Deep Work', color: 'text-ocean-600', bg: 'bg-ocean-50', border: 'border-ocean-200' },
  { key: 'short_task', label: 'Short Tasks', color: 'text-terracotta-600', bg: 'bg-terracotta-50', border: 'border-terracotta-200' },
  { key: 'maintenance', label: 'Maintenance', color: 'text-moss-600', bg: 'bg-moss-50', border: 'border-moss-200' },
] as const

export function DayDetail() {
  const { date } = useParams<{ date: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const todayStr = new Date().toLocaleDateString('en-CA')
  const isFuture = !!date && date > todayStr

  const { data: day, isLoading, isError } = useQuery({
    queryKey: ['day', date],
    queryFn: () => dayApi.getByDate(date!),
    enabled: !!date,
  })

  const toggleStatus = useMutation({
    mutationFn: (task: Task) =>
      taskApi.setStatus(task.id, task.status === 'completed' ? 'pending' : 'completed'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['day', date] })
      qc.invalidateQueries({ queryKey: ['days', 'all'] })
    },
  })

  const [addingCategory, setAddingCategory] = useState<Task['category'] | null>(null)
  const [newTaskTitle, setNewTaskTitle] = useState('')

  const createTask = useMutation({
    mutationFn: (category: Task['category']) =>
      taskApi.create({ day_id: day!.id, category, title: newTaskTitle.trim() }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['day', date] })
      qc.invalidateQueries({ queryKey: ['days', 'all'] })
      setNewTaskTitle('')
      setAddingCategory(null)
    },
  })

  const deleteTask = useMutation({
    mutationFn: (id: number) => taskApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['day', date] })
      qc.invalidateQueries({ queryKey: ['days', 'all'] })
    },
  })

  function handleAddTask(category: Task['category']) {
    if (!newTaskTitle.trim() || !day) return
    createTask.mutate(category)
  }

  const completedCount = day?.tasks.filter(t => t.status === 'completed').length ?? 0
  const totalCount = day?.tasks.length ?? 0
  const completionRate = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0

  return (
    <div className="flex min-h-screen bg-stone-25">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-stone-200 px-8 py-5 flex items-center justify-between flex-shrink-0">
          <div>
            <button
              onClick={() => navigate('/calendar')}
              className="text-sm text-stone-400 hover:text-stone-600 mb-2 flex items-center gap-1 transition-colors"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10 4L6 8L10 12" />
              </svg>
              Back to Calendar
            </button>
            {day && (
              <>
                <h1 className="text-xl font-semibold text-stone-800">
                  {new Date(day.date + 'T12:00:00').toLocaleDateString('en-US', {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </h1>
                {isFuture && (
                  <span className="mt-1 inline-block text-xs font-medium text-ocean-600 bg-ocean-50 px-2 py-0.5 rounded-full">
                    Planning
                  </span>
                )}
              </>
            )}
          </div>

          {/* Completion stats */}
          {day && totalCount > 0 && (
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-2xl font-semibold text-stone-800 tabular-nums">
                  {completedCount}<span className="text-stone-400">/{totalCount}</span>
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
                    stroke="#e7e5e4"
                    strokeWidth="4"
                  />
                  <circle
                    cx="24"
                    cy="24"
                    r="20"
                    fill="none"
                    stroke={completionRate === 100 ? '#4a8a4a' : '#e86b3a'}
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeDasharray={`${completionRate * 1.256} 125.6`}
                    className="transition-all duration-500"
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-stone-600">
                  {completionRate}%
                </span>
              </div>
            </div>
          )}
        </header>

        {/* Content */}
        <main className="flex-1 p-8 max-w-3xl">
          {isLoading && (
            <div className="flex items-center justify-center h-48 text-stone-400 text-sm">
              Loading...
            </div>
          )}

          {isError && (
            <div className="bg-terracotta-50 border border-terracotta-200 rounded-2xl p-6 text-center">
              <p className="text-terracotta-600">Could not load this day. Please try again.</p>
            </div>
          )}

          {day && (
            <div className="space-y-8 animate-fade-in">
              {categories.map(cat => {
                const tasks = day.tasks.filter(t => t.category === cat.key)
                if (tasks.length === 0) {
                  return (
                    <div key={cat.key}>
                      <div className="flex items-center justify-between mb-3">
                        <h2 className={`text-sm font-semibold uppercase tracking-wide ${cat.color}`}>
                          {cat.label}
                        </h2>
                      </div>
                      <div className={`rounded-2xl border ${cat.border} ${cat.bg} px-4 pt-2 pb-3`}>
                        <AddTaskForm
                          category={cat.key}
                          isOpen={addingCategory === cat.key}
                          title={newTaskTitle}
                          onOpen={() => { setAddingCategory(cat.key); setNewTaskTitle('') }}
                          onTitleChange={setNewTaskTitle}
                          onSubmit={() => handleAddTask(cat.key)}
                          onCancel={() => { setAddingCategory(null); setNewTaskTitle('') }}
                        />
                      </div>
                    </div>
                  )
                }

                const catCompleted = tasks.filter(t => t.status === 'completed').length

                return (
                  <div key={cat.key}>
                    <div className="flex items-center justify-between mb-3">
                      <h2 className={`text-sm font-semibold uppercase tracking-wide ${cat.color}`}>
                        {cat.label}
                      </h2>
                      <span className="text-xs text-stone-400 tabular-nums">
                        {catCompleted}/{tasks.length}
                      </span>
                    </div>
                    <div className={`space-y-2 rounded-2xl border ${cat.border} ${cat.bg} p-4`}>
                      {tasks.map(task => (
                        <div
                          key={task.id}
                          className="group bg-white rounded-xl border border-stone-100 p-4 flex items-center gap-3 shadow-sm"
                        >
                          <button
                            onClick={() => !isFuture && toggleStatus.mutate(task)}
                            disabled={isFuture}
                            title={isFuture ? "Can't complete a future task" : undefined}
                            className={`w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center transition-colors ${
                              task.status === 'completed'
                                ? 'bg-moss-500'
                                : 'bg-stone-200'
                            } ${isFuture ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer hover:opacity-80'}`}
                          >
                            {task.status === 'completed' && (
                              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="white" strokeWidth="2">
                                <path d="M2 6L5 9L10 3" strokeLinecap="round" strokeLinejoin="round" />
                              </svg>
                            )}
                          </button>
                          <span
                            className={`text-sm transition-colors ${
                              task.status === 'completed'
                                ? 'line-through text-stone-400'
                                : 'text-stone-800'
                            }`}
                          >
                            {task.title}
                          </span>
                          {task.description && (
                            <span className="text-xs text-stone-400 truncate">
                              — {task.description}
                            </span>
                          )}
                          <button
                            onClick={() => deleteTask.mutate(task.id)}
                            className="ml-auto opacity-0 group-hover:opacity-100 text-stone-300 hover:text-red-400 transition-colors"
                            title="Delete task"
                          >
                            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
                              <path d="M2 3.5h10M5.5 3.5V2.5h3v1M3.5 3.5l.5 8h6l.5-8" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                          </button>
                        </div>
                      ))}
                      <AddTaskForm
                        category={cat.key}
                        isOpen={addingCategory === cat.key}
                        title={newTaskTitle}
                        onOpen={() => { setAddingCategory(cat.key); setNewTaskTitle('') }}
                        onTitleChange={setNewTaskTitle}
                        onSubmit={() => handleAddTask(cat.key)}
                        onCancel={() => { setAddingCategory(null); setNewTaskTitle('') }}
                        mt
                      />
                    </div>
                  </div>
                )
              })}


            </div>
          )}
        </main>
      </div>
    </div>
  )
}
