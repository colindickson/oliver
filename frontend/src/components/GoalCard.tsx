import type { Goal } from '../api/client'

interface Props {
  goal: Goal
  isSelected: boolean
  isFocusGoal?: boolean
  isSubGoal?: boolean
  onClick: () => void
  onSetFocus?: () => void
  onArchive?: () => void
  onUnarchive?: () => void
}

function isOverdue(targetDate: string | null): boolean {
  if (!targetDate) return false
  return new Date(targetDate) < new Date(new Date().toISOString().slice(0, 10))
}

export function GoalCard({ goal, isSelected, isFocusGoal, isSubGoal, onClick, onSetFocus, onArchive, onUnarchive }: Props) {
  const overdue = goal.status === 'active' && isOverdue(goal.target_date)
  const isCompleted = goal.status === 'completed'
  const hasSubGoals = goal.sub_goal_count > 0

  function handleSetFocus(e: React.MouseEvent) {
    e.stopPropagation()
    onSetFocus?.()
  }

  function handleArchive(e: React.MouseEvent) {
    e.stopPropagation()
    onArchive?.()
  }

  function handleUnarchive(e: React.MouseEvent) {
    e.stopPropagation()
    onUnarchive?.()
  }

  // Ring sizing: sub-goal uses a slightly smaller ring
  const ringSize = isSubGoal ? 'w-7 h-7' : 'w-9 h-9'
  const ringViewBox = isSubGoal ? '0 0 28 28' : '0 0 36 36'
  const ringCx = isSubGoal ? '14' : '18'
  const ringCy = isSubGoal ? '14' : '18'
  const ringR = isSubGoal ? 12 : 16
  const circumference = 2 * Math.PI * ringR
  const strokeDash = `${goal.progress_pct * circumference / 100} ${circumference}`
  const ringColor = isCompleted ? '#4a8a4a' : '#e86b3a'
  const strokeWidth = isSubGoal ? '2.5' : '3'

  // Card padding/rounding: sub-goal is more compact
  const cardClass = isSubGoal
    ? 'w-full text-left px-2.5 py-2 rounded-lg border transition-all'
    : 'w-full text-left px-3 py-3 rounded-xl border transition-all'

  const subGoalLabel = hasSubGoals
    ? goal.sub_goal_count === 1
      ? '1 sub-goal'
      : `${goal.sub_goal_count} sub-goals`
    : null

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick()
        }
      }}
      className={`${cardClass} cursor-pointer ${
        isSelected
          ? 'border-terracotta-400 bg-terracotta-50/60 dark:bg-terracotta-900/20 dark:border-terracotta-600'
          : 'border-stone-200 bg-white hover:border-stone-300 hover:shadow-sm dark:bg-stone-800 dark:border-stone-700 dark:hover:border-stone-600'
      } ${isCompleted ? 'opacity-60' : ''}`}
    >
      <div className="flex items-center gap-2.5">
        {/* Progress ring */}
        <div className={`relative flex-shrink-0 ${ringSize}`}>
          <svg className={`${ringSize} -rotate-90`} viewBox={ringViewBox}>
            <circle cx={ringCx} cy={ringCy} r={ringR} fill="none" stroke="currentColor" strokeWidth={strokeWidth} className="text-stone-100 dark:text-stone-700" />
            <circle cx={ringCx} cy={ringCy} r={ringR} fill="none" stroke={ringColor} strokeWidth={strokeWidth} strokeLinecap="round"
              strokeDasharray={strokeDash} className="transition-all duration-500" />
          </svg>
          <span className={`absolute inset-0 flex items-center justify-center font-mono font-medium text-stone-500 dark:text-stone-400 rotate-0 ${isSubGoal ? 'text-[8px]' : 'text-[9px]'}`}>
            {goal.progress_pct}%
          </span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-0.5">
            {isFocusGoal && (
              <div className="w-1.5 h-1.5 rounded-full bg-terracotta-500 flex-shrink-0" title="Focus goal" />
            )}
            <span className={`font-medium leading-snug truncate ${
              isSubGoal ? 'text-xs' : 'text-sm'
            } ${
              isCompleted ? 'text-stone-400 line-through dark:text-stone-500' : 'text-stone-800 dark:text-stone-100'
            }`}>
              {goal.title}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-1">
            {/* Sub-goal count badge (only on parent cards) */}
            {subGoalLabel && (
              <span className="font-mono text-[10px] px-1.5 py-0.5 rounded-full bg-terracotta-100 dark:bg-terracotta-900/30 text-terracotta-600 dark:text-terracotta-400 border border-terracotta-200 dark:border-terracotta-700 flex-shrink-0">
                {subGoalLabel}
              </span>
            )}
            {goal.tags.slice(0, 3).map(tag => (
              <span key={tag} className="font-mono text-[10px] text-stone-400 dark:text-stone-500">#{tag}</span>
            ))}
            {goal.tags.length > 3 && (
              <span className="text-[10px] text-stone-400 dark:text-stone-500">+{goal.tags.length - 3}</span>
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
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-0.5 flex-shrink-0">
          {onSetFocus && !isFocusGoal && goal.status === 'active' && (
            <button onClick={handleSetFocus} className="p-1 rounded hover:bg-terracotta-100 dark:hover:bg-terracotta-900/30 text-stone-400 hover:text-terracotta-500 transition-colors" title="Set as focus goal">
              <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="8" cy="8" r="6" /><circle cx="8" cy="8" r="3" /><circle cx="8" cy="8" r="1" />
              </svg>
            </button>
          )}
          {onArchive && (
            <button onClick={handleArchive} className="p-1 rounded hover:bg-stone-100 dark:hover:bg-stone-700 text-stone-400 hover:text-stone-600 transition-colors" title="Archive goal">
              <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="2" y="3" width="12" height="2" rx="0.5" /><path d="M3 5v7.5a1.5 1.5 0 001.5 1.5h7a1.5 1.5 0 001.5-1.5V5" /><path d="M6.5 8h3" strokeLinecap="round" />
              </svg>
            </button>
          )}
          {onUnarchive && (
            <button onClick={handleUnarchive} className="p-1 rounded hover:bg-terracotta-100 dark:hover:bg-terracotta-900/30 text-stone-400 hover:text-terracotta-500 transition-colors" title="Unarchive goal">
              <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M2 8h12M8 2l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
