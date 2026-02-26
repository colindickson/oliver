import type { Goal } from '../api/client'

interface Props {
  goal: Goal
  isSelected: boolean
  onClick: () => void
}

function isOverdue(targetDate: string | null): boolean {
  if (!targetDate) return false
  return new Date(targetDate) < new Date(new Date().toISOString().slice(0, 10))
}

export function GoalCard({ goal, isSelected, onClick }: Props) {
  const overdue = goal.status === 'active' && isOverdue(goal.target_date)
  const isCompleted = goal.status === 'completed'

  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-3 py-3 rounded-xl border transition-all ${
        isSelected
          ? 'border-terracotta-400 bg-terracotta-50/60 dark:bg-terracotta-900/20 dark:border-terracotta-600'
          : 'border-stone-200 bg-white hover:border-stone-300 hover:shadow-sm dark:bg-stone-800 dark:border-stone-700 dark:hover:border-stone-600'
      } ${isCompleted ? 'opacity-60' : ''}`}
    >
      {/* Title row */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className={`text-sm font-medium leading-snug ${
          isCompleted
            ? 'text-stone-400 line-through dark:text-stone-500'
            : 'text-stone-800 dark:text-stone-100'
        }`}>
          {goal.title}
        </span>
        {isCompleted && (
          <span className="flex-shrink-0 mt-0.5">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" className="text-moss-500 dark:text-moss-400">
              <path d="M2 7l4 4 6-6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
        )}
      </div>

      {/* Progress bar */}
      {goal.total_tasks > 0 && (
        <div className="mb-2">
          <div className="h-1.5 bg-stone-100 dark:bg-stone-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                isCompleted
                  ? 'bg-moss-500 dark:bg-moss-600'
                  : 'bg-gradient-to-r from-terracotta-400 to-terracotta-500'
              }`}
              style={{ width: `${goal.progress_pct}%` }}
            />
          </div>
          <div className="flex items-center justify-between mt-1">
            <span className="text-[11px] text-stone-400 dark:text-stone-500">
              {goal.completed_tasks}/{goal.total_tasks} tasks
            </span>
            <span className="text-[11px] text-stone-400 dark:text-stone-500 tabular-nums">
              {goal.progress_pct}%
            </span>
          </div>
        </div>
      )}

      {/* Footer: tags + target date */}
      <div className="flex flex-wrap items-center gap-1.5">
        {goal.tags.slice(0, 3).map(tag => (
          <span
            key={tag}
            className="text-[10px] px-1.5 py-0.5 rounded-full bg-stone-100 text-stone-500 dark:bg-stone-700 dark:text-stone-400"
          >
            #{tag}
          </span>
        ))}
        {goal.tags.length > 3 && (
          <span className="text-[10px] text-stone-400 dark:text-stone-500">
            +{goal.tags.length - 3}
          </span>
        )}
        {goal.target_date && (
          <span className={`ml-auto text-[10px] flex items-center gap-0.5 ${
            overdue ? 'text-red-500 dark:text-red-400' : 'text-stone-400 dark:text-stone-500'
          }`}>
            {overdue && (
              <svg width="10" height="10" viewBox="0 0 14 14" fill="currentColor">
                <path d="M7 1L13.9 13H0.1L7 1zm0 3.5v4h0V4.5zm0 5.5a.75.75 0 100 1.5A.75.75 0 007 10z" />
              </svg>
            )}
            {goal.target_date}
          </span>
        )}
      </div>
    </button>
  )
}
