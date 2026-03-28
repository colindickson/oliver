import { useState } from 'react'
import { CalendarPicker } from './CalendarPicker'
import { formatRollDate } from '../utils/format'

interface Props {
  onConfirm: (targetDate: string) => void
  onCancel: () => void
}

export function RollForwardModal({ onConfirm, onCancel }: Props) {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  const minDate = tomorrow.toISOString().slice(0, 10)

  const [selectedDate, setSelectedDate] = useState('')

  return (
    <div role="dialog" aria-modal="true" className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onCancel}>
      <div
        className="bg-stone-800 rounded-2xl shadow-xl p-5 w-96 space-y-4"
        onClick={e => e.stopPropagation()}
      >
        <h2 className="text-sm font-semibold text-stone-200">Roll forward to…</h2>

        <CalendarPicker
          selectedDate={selectedDate}
          onSelectDate={setSelectedDate}
          minDate={minDate}
        />

        {/* Actions */}
        <div className="flex gap-2 pt-1">
          <button
            type="button"
            disabled={!selectedDate}
            onClick={() => onConfirm(selectedDate)}
            className="flex-1 text-sm bg-stone-700 text-white rounded-lg px-4 py-2 hover:bg-stone-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {selectedDate ? `Roll Forward → ${formatRollDate(selectedDate)}` : 'Roll Forward'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="text-sm text-stone-400 hover:text-stone-200 transition-colors px-3"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
