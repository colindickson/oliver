import { useState } from 'react'

interface Props {
  onConfirm: (targetDate: string) => void
  onCancel: () => void
}

function getTomorrow(): string {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().split('T')[0]
}

export function RollForwardModal({ onConfirm, onCancel }: Props) {
  const tomorrow = getTomorrow()
  const [selectedDate, setSelectedDate] = useState(tomorrow)

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={onCancel}>
      <div
        className="bg-white dark:bg-stone-800 rounded-2xl shadow-xl p-6 w-80 space-y-4"
        onClick={e => e.stopPropagation()}
      >
        <h2 className="text-sm font-semibold text-stone-700 dark:text-stone-200">Roll forward to…</h2>
        <input
          type="date"
          min={tomorrow}
          value={selectedDate}
          onChange={e => setSelectedDate(e.target.value)}
          className="w-full text-sm border border-stone-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent dark:bg-stone-700 dark:border-stone-600 dark:text-stone-100"
        />
        <div className="flex gap-2 pt-1">
          <button
            type="button"
            disabled={!selectedDate || selectedDate < tomorrow}
            onClick={() => onConfirm(selectedDate)}
            className="flex-1 text-sm bg-stone-800 text-white rounded-lg px-4 py-2 hover:bg-stone-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all dark:bg-stone-600 dark:hover:bg-stone-500"
          >
            Roll Forward
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="text-sm text-stone-400 hover:text-stone-600 transition-colors px-3 dark:text-stone-500 dark:hover:text-stone-300"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
