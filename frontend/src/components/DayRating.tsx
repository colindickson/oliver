import { useState } from 'react'
import type { DayRating } from '../api/client'

interface DayRatingProps {
  dayId: number
  initialRating: DayRating | null
  onSave: (dayId: number, rating: Partial<Omit<DayRating, 'id' | 'day_id'>>) => Promise<unknown>
}

type Dimension = 'focus' | 'energy' | 'satisfaction'

const DIMENSIONS: { key: Dimension; label: string }[] = [
  { key: 'focus', label: 'Focus' },
  { key: 'energy', label: 'Energy' },
  { key: 'satisfaction', label: 'Satisfaction' },
]

function StarRow({
  label,
  value,
  onChange,
}: {
  label: string
  value: number | null
  onChange: (v: number | null) => void
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-stone-500 dark:text-stone-400 w-24 flex-shrink-0">{label}</span>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map(star => {
          const filled = value !== null && star <= value
          return (
            <button
              key={star}
              type="button"
              onClick={() => onChange(value === star ? null : star)}
              className="w-6 h-6 transition-transform hover:scale-110 focus:outline-none"
              title={`${label}: ${star}`}
            >
              <svg
                viewBox="0 0 24 24"
                fill={filled ? 'currentColor' : 'none'}
                stroke="currentColor"
                strokeWidth="1.5"
                className={filled ? 'text-terracotta-500' : 'text-stone-300'}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M11.48 3.499a.562.562 0 0 1 1.04 0l2.125 5.111a.563.563 0 0 0 .475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 0 0-.182.557l1.285 5.385a.562.562 0 0 1-.84.61l-4.725-2.885a.562.562 0 0 0-.586 0L6.982 20.54a.562.562 0 0 1-.84-.61l1.285-5.386a.562.562 0 0 0-.182-.557l-4.204-3.602a.562.562 0 0 1 .321-.988l5.518-.442a.563.563 0 0 0 .475-.345L11.48 3.5Z"
                />
              </svg>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export function DayRating({ dayId, initialRating, onSave }: DayRatingProps) {
  const [focus, setFocus] = useState<number | null>(initialRating?.focus ?? null)
  const [energy, setEnergy] = useState<number | null>(initialRating?.energy ?? null)
  const [satisfaction, setSatisfaction] = useState<number | null>(
    initialRating?.satisfaction ?? null,
  )

  async function handleChange(dimension: Dimension, value: number | null) {
    const next = { focus, energy, satisfaction, [dimension]: value }
    if (dimension === 'focus') setFocus(value)
    if (dimension === 'energy') setEnergy(value)
    if (dimension === 'satisfaction') setSatisfaction(value)
    await onSave(dayId, next)
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-stone-600 dark:text-stone-300 uppercase tracking-wide">
        Day Rating
      </h3>
      <div className="bg-white dark:bg-stone-700 dark:border-stone-600/50 rounded-xl border border-stone-200 px-4 py-3 space-y-2.5">
        <StarRow label="Focus" value={focus} onChange={v => handleChange('focus', v)} />
        <StarRow label="Energy" value={energy} onChange={v => handleChange('energy', v)} />
        <StarRow
          label="Satisfaction"
          value={satisfaction}
          onChange={v => handleChange('satisfaction', v)}
        />
      </div>
    </div>
  )
}
