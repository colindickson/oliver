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
    .slice(0, 16) // "YYYY-MM-DDTHH:mm"

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
      className="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
      onClick={handleBackdropClick}
    >
      <div
        className="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm mx-4"
        onClick={handleDialogClick}
      >
        <h2 className="text-base font-semibold text-gray-900 mb-4">Set Reminder</h2>
        <p className="text-sm text-gray-500 mb-4 truncate">{task.title}</p>

        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-gray-500 block mb-1">When</label>
            <input
              type="datetime-local"
              value={remindAt}
              onChange={e => setRemindAt(e.target.value)}
              className="w-full text-sm border border-gray-200 rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 block mb-1">Message</label>
            <input
              type="text"
              value={message}
              onChange={e => setMessage(e.target.value)}
              className="w-full text-sm border border-gray-200 rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
          </div>
        </div>

        <div className="flex gap-2 mt-5">
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={createReminder.isPending}
            className="flex-1 bg-blue-600 text-white text-sm rounded-lg py-2 hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {createReminder.isPending ? 'Saving...' : 'Set Reminder'}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-4 text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
