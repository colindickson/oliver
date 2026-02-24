import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { Task } from '../api/client'
import { useTaskEdit } from '../hooks/useTaskEdit'
import { ConfirmableDelete } from './ConfirmableDelete'
import { ReminderDialog } from './ReminderDialog'
import { TagInput } from './TagInput'

interface Props {
  task: Task
  onComplete: (task: Task) => void
  onDelete: (id: number) => void
  onMoveToBacklog?: (task: Task) => void
}

export function TaskCard({ task, onComplete, onDelete, onMoveToBacklog }: Props) {
  const isCompleted = task.status === 'completed'
  const [showReminder, setShowReminder] = useState(false)

  const {
    editing,
    editTitle,
    editDescription,
    editTags,
    saving,
    openEdit,
    saveEdit,
    cancelEdit,
    setEditTitle,
    setEditDescription,
    setEditTags,
  } = useTaskEdit({ task })

  if (editing) {
    return (
      <div className="p-3 rounded-xl border border-terracotta-200 bg-white dark:bg-stone-800 dark:border-terracotta-700/40 shadow-sm space-y-2">
        <input
          autoFocus
          type="text"
          value={editTitle}
          onChange={e => setEditTitle(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') void saveEdit()
            if (e.key === 'Escape') cancelEdit()
          }}
          className="w-full text-sm border border-stone-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent dark:bg-stone-700 dark:border-stone-600 dark:text-stone-100"
        />
        <textarea
          value={editDescription}
          onChange={e => setEditDescription(e.target.value)}
          placeholder="Description (optional)"
          rows={2}
          className="w-full text-sm border border-stone-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent resize-none dark:bg-stone-700 dark:border-stone-600 dark:text-stone-100 dark:placeholder-stone-400"
        />
        <TagInput value={editTags} onChange={setEditTags} />
        <div className="flex gap-2 pt-0.5">
          <button
            type="button"
            onClick={() => void saveEdit()}
            disabled={saving || !editTitle.trim()}
            className="text-xs bg-stone-800 text-white rounded-lg px-3 py-1.5 hover:bg-stone-700 disabled:opacity-50 transition-all dark:bg-stone-600 dark:hover:bg-stone-500"
          >
            Save
          </button>
          <button
            type="button"
            onClick={cancelEdit}
            className="text-xs text-stone-400 hover:text-stone-600 transition-colors px-2 dark:text-stone-500 dark:hover:text-stone-300"
          >
            Cancel
          </button>
        </div>
      </div>
    )
  }

  return (
    <>
      <div
        className={`group p-3 rounded-xl border border-stone-100 bg-white dark:bg-stone-800 dark:border-stone-700/60 shadow-sm flex items-start gap-3 transition-all duration-200 hover:shadow-soft ${
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
            className={`text-sm font-medium text-stone-800 dark:text-stone-100 transition-colors ${
              isCompleted ? 'line-through text-stone-400' : ''
            }`}
          >
            {task.title}
          </p>
          {task.description && (
            <p className="text-xs text-stone-400 mt-0.5 truncate">{task.description}</p>
          )}
          {task.tags && task.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {task.tags.map(tag => (
                <Link
                  key={tag}
                  to={`/tags/${encodeURIComponent(tag)}`}
                  onClick={e => e.stopPropagation()}
                  className="text-xs px-1.5 py-0.5 rounded-full bg-stone-100 text-stone-500 hover:bg-terracotta-50 hover:text-terracotta-600 transition-colors dark:bg-stone-700 dark:text-stone-400 dark:hover:bg-terracotta-900/30 dark:hover:text-terracotta-300"
                >
                  #{tag}
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {/* Edit */}
          <button
            type="button"
            onClick={openEdit}
            className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-stone-500 hover:bg-stone-50 rounded transition-colors opacity-0 group-hover:opacity-100 dark:text-stone-600 dark:hover:text-stone-300 dark:hover:bg-stone-700"
            aria-label="Edit task"
          >
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M9 2L11 4L5 10H3V8L9 2Z" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          {/* Set reminder */}
          <button
            type="button"
            onClick={() => setShowReminder(true)}
            className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-amber-400 hover:bg-amber-50 rounded transition-colors dark:text-stone-600 dark:hover:text-amber-300 dark:hover:bg-stone-700"
            aria-label="Set reminder"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M7 12.5C7 12.5 11 10 11 6C11 3.5 9.2 1.5 7 1.5C4.8 1.5 3 3.5 3 6C3 10 7 12.5 7 12.5Z" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M7 4V6" strokeLinecap="round" />
            </svg>
          </button>

          {/* Move to backlog */}
          {onMoveToBacklog && (
            <button
              type="button"
              onClick={() => onMoveToBacklog(task)}
              className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-ocean-400 hover:bg-ocean-50 rounded transition-colors opacity-0 group-hover:opacity-100 dark:text-stone-600 dark:hover:text-ocean-300 dark:hover:bg-stone-700"
              aria-label="Send to backlog"
              title="Send to backlog"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M2 2h10v10H2z" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M5 5h4M5 7h4M5 9h2" strokeLinecap="round" />
              </svg>
            </button>
          )}

          {/* Delete */}
          <ConfirmableDelete onConfirm={() => onDelete(task.id)} />
        </div>
      </div>

      {showReminder && (
        <ReminderDialog task={task} onClose={() => setShowReminder(false)} />
      )}
    </>
  )
}
