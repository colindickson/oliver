import { useTagFilters, type PeriodOption } from '../hooks/useTagFilters'

const PERIOD_OPTIONS: { label: string; value: PeriodOption }[] = [
  { label: '7d', value: 7 },
  { label: '30d', value: 30 },
  { label: '90d', value: 90 },
  { label: 'All', value: 'all' },
]

interface PeriodSelectorProps {
  value: PeriodOption
  onChange: (value: PeriodOption) => void
}

export function PeriodSelector({ value, onChange }: PeriodSelectorProps) {
  return (
    <div className="flex items-center bg-stone-100 dark:bg-stone-700 rounded-xl p-1 gap-0.5">
      {PERIOD_OPTIONS.map(({ label, value: optValue }) => (
        <button
          key={label}
          onClick={() => onChange(optValue)}
          className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
            value === optValue
              ? 'bg-white dark:bg-stone-600 text-stone-800 dark:text-stone-100 shadow-soft'
              : 'text-stone-500 dark:text-stone-400 hover:text-stone-700 dark:hover:text-stone-200'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
