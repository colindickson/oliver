import { useEffect, useState } from 'react'
import { dayApi } from '../api/client'
import { CalendarPicker } from './CalendarPicker'
import { formatRollDate, toLocalDateStr } from '../utils/format'

interface ContinueModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: (targetDate: string) => void
  taskTitle?: string
}

export function ContinueModal({ isOpen, onClose, onConfirm, taskTitle }: ContinueModalProps) {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  const minDate = toLocalDateStr(tomorrow)

  const [selectedDate, setSelectedDate] = useState('')

  useEffect(() => {
    if (!isOpen) return
    dayApi.getNextWorkingDay().then(({ date }) => setSelectedDate(date))
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-stone-800 rounded-2xl shadow-xl p-5 w-96 space-y-4"
        onClick={e => e.stopPropagation()}
      >
        <div>
          <h2 className="text-sm font-semibold text-stone-200">Continue task</h2>
          {taskTitle && (
            <p className="text-xs text-stone-400 mt-1 truncate">{taskTitle}</p>
          )}
        </div>

        <CalendarPicker
          selectedDate={selectedDate}
          onSelectDate={setSelectedDate}
          minDate={minDate}
        />

        <div className="flex gap-2 pt-1">
          <button
            type="button"
            disabled={!selectedDate}
            onClick={() => onConfirm(selectedDate)}
            className="flex-1 text-sm bg-stone-700 text-white rounded-lg px-4 py-2 hover:bg-stone-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {selectedDate ? `Continue → ${formatRollDate(selectedDate)}` : 'Continue'}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="text-sm text-stone-400 hover:text-stone-200 transition-colors px-3"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
