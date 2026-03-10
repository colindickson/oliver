import { useNavigate } from 'react-router-dom'
import { useFocusGoal } from '../hooks/useFocusGoal'
import { useMobile } from '../contexts/MobileContext'

export function FocusGoalBanner() {
  const navigate = useNavigate()
  const { focusGoal, isLoading } = useFocusGoal()
  const isMobile = useMobile()

  if (isLoading || !focusGoal) {
    return null
  }

  const handleClick = () => {
    navigate(`/goals?id=${focusGoal.id}`)
  }

  return (
    <button
      onClick={handleClick}
      className={`w-full bg-gradient-to-r from-terracotta-500/10 to-terracotta-400/5 dark:from-terracotta-500/20 dark:to-terracotta-400/10 border-b border-terracotta-200/50 dark:border-terracotta-800/30 flex items-center justify-between group hover:from-terracotta-500/15 hover:to-terracotta-400/10 dark:hover:from-terracotta-500/25 dark:hover:to-terracotta-400/15 transition-colors ${
        isMobile ? 'px-4 py-2' : 'px-8 py-2.5'
      }`}
    >
      <div className="flex items-center gap-2 min-w-0">
        <svg
          width={isMobile ? 14 : 16}
          height={isMobile ? 14 : 16}
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          className="text-terracotta-500 dark:text-terracotta-400 flex-shrink-0"
        >
          <circle cx="8" cy="8" r="6" />
          <circle cx="8" cy="8" r="3" />
          <circle cx="8" cy="8" r="1" fill="currentColor" stroke="none" />
        </svg>
        <span className={`font-medium text-stone-700 dark:text-stone-200 truncate ${isMobile ? 'text-xs' : 'text-sm'}`}>
          {focusGoal.title}
        </span>
        {!isMobile && focusGoal.target_date && (
          <span className="text-xs text-stone-400 dark:text-stone-500 flex-shrink-0">
            {focusGoal.target_date}
          </span>
        )}
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className={`text-stone-500 dark:text-stone-400 tabular-nums ${isMobile ? 'text-[10px]' : 'text-xs'}`}>
          {focusGoal.completed_tasks}/{focusGoal.total_tasks}
        </span>
        <div className={`${isMobile ? 'w-12' : 'w-16'} h-1.5 bg-stone-200 dark:bg-stone-700 rounded-full overflow-hidden`}>
          <div
            className="h-full bg-terracotta-500 dark:bg-terracotta-400 rounded-full transition-all"
            style={{ width: `${focusGoal.progress_pct}%` }}
          />
        </div>
        <span className={`font-medium text-terracotta-600 dark:text-terracotta-400 tabular-nums ${isMobile ? 'text-[10px] w-6' : 'text-xs w-8'} text-right`}>
          {focusGoal.progress_pct}%
        </span>
        <svg
          width={isMobile ? 12 : 14}
          height={isMobile ? 12 : 14}
          viewBox="0 0 14 14"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          className="text-stone-400 dark:text-stone-500 group-hover:text-terracotta-500 dark:group-hover:text-terracotta-400 transition-colors"
        >
          <path d="M5 3l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    </button>
  )
}
