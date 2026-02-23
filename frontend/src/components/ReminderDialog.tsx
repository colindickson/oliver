import { useState } from 'react'
import { useReminders } from '../hooks/useReminders'
import type { Task } from '../api/client'

interface Props {
  task: Task
  onClose: () => void
}

export function ReminderDialog({ task, onClose }: Props) {
  const { createReminder } = useReminders()

  const defaultTime = new Date(Date.now() + 30 * 60 * 1000)
    .toISOString()
    .slice(0, 16)

  const [remindAt, setRemindAt] = useState(defaultTime)
  const [message, setMessage] = useState(`Reminder: ${task.title}`)

  async function handleSave() {
    await createReminder.mutateAsync({
      task_id: task.id,
      remind_at: new Date(remindAt).toISOString(),
      message,
    })
    onClose()
  }

  function handleBackdropClick() {
    onClose()
  }

  function handleDialogClick(e: React.MouseEvent) {
    e.stopPropagation()
  }

  return (
    <div
      className="fixed inset-0 bg-stone-900/50 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in"
      onClick={handleBackdropClick}
    >
      <div
        className="bg-white rounded-2xl shadow-soft-lg p-6 w-full max-w-sm mx-4 animate-slide-up dark:bg-stone-700 dark:border dark:border-amber-800/40"
        onClick={handleDialogClick}
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="#d97706" strokeWidth="1.5">
              <path d="M10 17C10 17 15 13.5 15 9C15 5.5 12.5 3 10 3C7.5 3 5 5.5 5 9C5 13.5 10 17 10 17Z" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M10 6V9" strokeLinecap="round" />
            </svg>
          </div>
          <div>
            <h2 className="text-base font-semibold text-stone-800 dark:text-stone-100">Set Reminder</h2>
            <p className="text-xs text-stone-400 truncate max-w-[200px]">{task.title}</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-xs font-medium text-stone-500 uppercase tracking-wider block mb-2">
              When
            </label>
            <input
              type="datetime-local"
              value={remindAt}
              onChange={e => setRemindAt(e.target.value)}
              className="w-full text-sm border border-stone-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent transition-shadow dark:bg-stone-600 dark:border-stone-500 dark:text-stone-100"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-stone-500 uppercase tracking-wider block mb-2">
              Message
            </label>
            <input
              type="text"
              value={message}
              onChange={e => setMessage(e.target.value)}
              className="w-full text-sm border border-stone-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent transition-shadow dark:bg-stone-600 dark:border-stone-500 dark:text-stone-100"
            />
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={createReminder.isPending}
            className="flex-1 bg-terracotta-600 text-white text-sm font-medium rounded-xl py-2.5 hover:bg-terracotta-500 disabled:opacity-50 transition-colors"
          >
            {createReminder.isPending ? 'Saving...' : 'Set Reminder'}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-5 text-sm text-stone-500 hover:text-stone-700 transition-colors dark:text-stone-400 dark:hover:text-stone-200"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
