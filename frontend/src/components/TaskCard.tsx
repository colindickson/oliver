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
        className={`p-3 rounded-xl border border-stone-100 bg-white shadow-sm flex items-start gap-3 transition-all duration-200 hover:shadow-soft ${
          isCompleted ? 'opacity-50' : 'opacity-100'
        }`}
      >
        {/* Complete toggle */}
        <button
          type="button"
          onClick={() => onComplete(task)}
          className={`mt-0.5 w-5 h-5 rounded-full border-2 flex-shrink-0 flex items-center justify-center transition-all duration-200 ${
            isCompleted
              ? 'bg-moss-500 border-moss-500'
              : 'border-stone-300 hover:border-moss-400 hover:bg-moss-50'
          }`}
          aria-label={isCompleted ? 'Mark incomplete' : 'Mark complete'}
        >
          {isCompleted && (
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="white" strokeWidth="2">
              <path d="M2 6L5 9L10 3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
        </button>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p
            className={`text-sm font-medium text-stone-800 transition-colors ${
              isCompleted ? 'line-through text-stone-400' : ''
            }`}
          >
            {task.title}
          </p>
          {task.description && (
            <p className="text-xs text-stone-400 mt-0.5 truncate">{task.description}</p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {/* Set reminder */}
          <button
            type="button"
            onClick={() => setShowReminder(true)}
            className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-amber-400 hover:bg-amber-50 rounded transition-colors"
            aria-label="Set reminder"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M7 12.5C7 12.5 11 10 11 6C11 3.5 9.2 1.5 7 1.5C4.8 1.5 3 3.5 3 6C3 10 7 12.5 7 12.5Z" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M7 4V6" strokeLinecap="round" />
            </svg>
          </button>

          {/* Delete */}
          <button
            type="button"
            onClick={() => onDelete(task.id)}
            className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-red-400 hover:bg-red-50 rounded transition-colors"
            aria-label="Delete task"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M3.5 4L4.5 12H9.5L10.5 4" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 4H12" strokeLinecap="round" />
              <path d="M5 4V2.5H9V4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>

      {showReminder && (
        <ReminderDialog task={task} onClose={() => setShowReminder(false)} />
      )}
    </>
  )
}
