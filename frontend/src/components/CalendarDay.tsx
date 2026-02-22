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

  // Color: gray if no tasks, color scale based on completion
  let bgClass = 'bg-stone-50 text-stone-300'
  if (total > 0) {
    if (pct >= 1) bgClass = 'bg-moss-500 text-white'
    else if (pct >= 0.67) bgClass = 'bg-amber-200 text-amber-900'
    else if (pct >= 0.33) bgClass = 'bg-stone-200 text-stone-700'
    else bgClass = 'bg-terracotta-200 text-terracotta-800'
  }

  return (
    <button
      onClick={onClick}
      disabled={total === 0}
      className={`
        aspect-square w-full flex flex-col items-center justify-center rounded-xl text-sm font-medium
        transition-all duration-200 hover:shadow-soft hover:-translate-y-0.5 disabled:cursor-default disabled:hover:translate-y-0 disabled:hover:shadow-none
        ${bgClass}
        ${isToday ? 'ring-2 ring-terracotta-500 ring-offset-2' : ''}
      `}
    >
      <span>{date.getDate()}</span>
      {total > 0 && (
        <span className="text-[10px] opacity-75">{completed}/{total}</span>
      )}
    </button>
  )
}
