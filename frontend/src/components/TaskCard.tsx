import { useState } from 'react'
import type { Task } from '../api/client'
import { ReminderDialog } from './ReminderDialog'

interface Props {
  task: Task
  onComplete: (task: Task) => void
  onDelete: (id: number) => void
}

export function TaskCard({ task, onComplete, onDelete }: Props) {
  const isCompleted = task.status === 'completed'
  const [showReminder, setShowReminder] = useState(false)

  return (
    <>
      <div
        className={`p-3 rounded-lg border bg-white shadow-sm flex items-start gap-3 transition-opacity ${
          isCompleted ? 'opacity-60' : 'opacity-100'
        }`}
      >
        {/* Complete toggle */}
        <button
          type="button"
          onClick={() => onComplete(task)}
          className={`mt-0.5 w-5 h-5 rounded-full border-2 flex-shrink-0 transition-colors ${
            isCompleted
              ? 'bg-green-500 border-green-500'
              : 'border-gray-300 hover:border-green-400'
          }`}
          aria-label={isCompleted ? 'Mark incomplete' : 'Mark complete'}
        />

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p
            className={`text-sm font-medium text-gray-900 ${
              isCompleted ? 'line-through text-gray-500' : ''
            }`}
          >
            {task.title}
          </p>
          {task.description && (
            <p className="text-xs text-gray-500 mt-0.5 truncate">{task.description}</p>
          )}
        </div>

        {/* Set reminder */}
        <button
          type="button"
          onClick={() => setShowReminder(true)}
          className="text-gray-300 hover:text-amber-400 transition-colors flex-shrink-0 text-xs leading-none mt-0.5"
          aria-label="Set reminder"
        >
          &#9993;
        </button>

        {/* Delete */}
        <button
          type="button"
          onClick={() => onDelete(task.id)}
          className="text-gray-300 hover:text-red-400 transition-colors flex-shrink-0 text-xs leading-none mt-0.5"
          aria-label="Delete task"
        >
          x
        </button>
      </div>

      {showReminder && (
        <ReminderDialog task={task} onClose={() => setShowReminder(false)} />
      )}
    </>
  )
}
