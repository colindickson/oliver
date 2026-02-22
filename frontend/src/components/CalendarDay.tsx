import type { Task } from '../api/client'

interface Props {
  date: Date
  tasks: Task[]
  isToday: boolean
  onClick: () => void
}

export function CalendarDay({ date, tasks, isToday, onClick }: Props) {
  const completed = tasks.filter(t => t.status === 'completed').length
  const total = tasks.length
  const pct = total > 0 ? completed / total : 0

  // Color: gray if no tasks, green scale based on completion
  let bgClass = 'bg-gray-50 text-gray-300'
  if (total > 0) {
    if (pct >= 1) bgClass = 'bg-green-500 text-white'
    else if (pct >= 0.67) bgClass = 'bg-green-300 text-green-900'
    else if (pct >= 0.33) bgClass = 'bg-amber-200 text-amber-900'
    else bgClass = 'bg-red-100 text-red-700'
  }

  return (
    <button
      onClick={onClick}
      disabled={total === 0}
      className={`
        aspect-square w-full flex flex-col items-center justify-center rounded-lg text-sm font-medium
        transition-all hover:ring-2 hover:ring-blue-300 disabled:cursor-default
        ${bgClass}
        ${isToday ? 'ring-2 ring-blue-500' : ''}
      `}
    >
      <span>{date.getDate()}</span>
      {total > 0 && (
        <span className="text-xs opacity-75">{completed}/{total}</span>
      )}
    </button>
  )
}
