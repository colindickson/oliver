import { useState } from 'react'
import type { Task } from '../api/client'
import { TaskCard } from './TaskCard'

type ColorKey = 'blue' | 'amber' | 'green'

interface Props {
  title: string
  category: Task['category']
  tasks: Task[]
  colorClass: ColorKey
  onAddTask: (title: string, description: string) => Promise<void>
  onComplete: (task: Task) => void
  onDelete: (id: number) => void
}

const headerColors: Record<ColorKey, string> = {
  blue: 'border-blue-400 text-blue-700',
  amber: 'border-amber-400 text-amber-700',
  green: 'border-green-400 text-green-700',
}

const buttonColors: Record<ColorKey, string> = {
  blue: 'bg-blue-50 text-blue-600 hover:bg-blue-100 border-blue-200',
  amber: 'bg-amber-50 text-amber-600 hover:bg-amber-100 border-amber-200',
  green: 'bg-green-50 text-green-600 hover:bg-green-100 border-green-200',
}

export function TaskColumn({
  title,
  category,
  tasks,
  colorClass,
  onAddTask,
  onComplete,
  onDelete,
}: Props) {
  const [adding, setAdding] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const categoryTasks = tasks.filter(t => t.category === category)
  const completedCount = categoryTasks.filter(t => t.status === 'completed').length

  async function handleAdd() {
    if (!newTitle.trim()) return
    setIsSubmitting(true)
    try {
      await onAddTask(newTitle.trim(), newDesc.trim())
      setNewTitle('')
      setNewDesc('')
      setAdding(false)
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      void handleAdd()
    }
    if (e.key === 'Escape') {
      setAdding(false)
      setNewTitle('')
      setNewDesc('')
    }
  }

  function handleCancel() {
    setAdding(false)
    setNewTitle('')
    setNewDesc('')
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Column header */}
      <div
        className={`flex items-center justify-between mb-4 pb-2 border-b-2 ${headerColors[colorClass]}`}
      >
        <h2 className="font-semibold text-sm uppercase tracking-wide">{title}</h2>
        <span className="text-xs text-gray-400">
          {completedCount}/{categoryTasks.length}
        </span>
      </div>

      {/* Task list */}
      <div className="flex flex-col gap-2 flex-1">
        {categoryTasks.map(task => (
          <TaskCard
            key={task.id}
            task={task}
            onComplete={onComplete}
            onDelete={onDelete}
          />
        ))}
      </div>

      {/* Add task area */}
      {adding ? (
        <div className="mt-3 space-y-2">
          <input
            autoFocus
            type="text"
            value={newTitle}
            onChange={e => setNewTitle(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Task title"
            className="w-full text-sm border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
          <input
            type="text"
            value={newDesc}
            onChange={e => setNewDesc(e.target.value)}
            onKeyDown={e => { if (e.key === 'Escape') handleCancel() }}
            placeholder="Description (optional)"
            className="w-full text-sm border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => void handleAdd()}
              disabled={isSubmitting || !newTitle.trim()}
              className="text-xs bg-gray-800 text-white rounded px-3 py-1 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
            >
              Add
            </button>
            <button
              type="button"
              onClick={handleCancel}
              className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setAdding(true)}
          className={`mt-3 w-full text-xs border rounded py-1.5 transition-colors ${buttonColors[colorClass]}`}
        >
          + Add task
        </button>
      )}
    </div>
  )
}
