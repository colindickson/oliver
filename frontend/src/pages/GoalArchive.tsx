import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { Sidebar } from '../components/Sidebar'
import { GoalCard } from '../components/GoalCard'
import { GoalDetail } from '../components/GoalDetail'
import { useArchivedGoals } from '../hooks/useArchivedGoals'
import { useMobile } from '../contexts/MobileContext'
import { MobileHeader } from '../components/MobileHeader'
import { BottomTabBar } from '../components/BottomTabBar'

export function GoalArchive() {
  const { goals, isError, unarchiveGoal } = useArchivedGoals()
  const [searchParams, setSearchParams] = useSearchParams()
  const [selectedGoalId, setSelectedGoalId] = useState<number | null>(() => {
    const id = searchParams.get('id')
    return id ? parseInt(id, 10) : null
  })
  const isMobile = useMobile()

  useEffect(() => {
    if (selectedGoalId !== null) {
      setSearchParams({ id: String(selectedGoalId) })
    } else {
      setSearchParams({})
    }
  }, [selectedGoalId, setSearchParams])

  const activeGoals = goals.filter(g => g.status === 'active')
  const completedGoals = goals.filter(g => g.status === 'completed')

  function handleUnarchive() {
    if (selectedGoalId !== null) {
      unarchiveGoal.mutate(selectedGoalId, {
        onSuccess: () => setSelectedGoalId(null),
      })
    }
  }

  if (isError) {
    if (isMobile) {
      return (
        <div className="flex flex-col h-screen bg-stone-900">
          <MobileHeader title="Archive" />
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <p className="text-stone-400 text-sm">Failed to load archived goals.</p>
          </div>
          <BottomTabBar />
        </div>
      )
    }
    return (
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <p className="text-stone-400 text-sm">Failed to load archived goals.</p>
        </div>
      </div>
    )
  }

  if (isMobile) {
    return (
      <div className="flex flex-col h-screen bg-stone-900">
        <MobileHeader title="Archive" />
        <div className="flex-1 overflow-y-auto pb-14">
          <div className="px-4 py-3 space-y-1.5">
            <div className="flex items-center justify-between py-2">
              <h1 className="text-base font-semibold text-stone-800 dark:text-stone-100">Archive</h1>
              <Link
                to="/goals"
                className="text-xs text-stone-400 hover:text-stone-600 dark:hover:text-stone-300 transition-colors"
              >
                Back to Goals
              </Link>
            </div>

            {goals.length === 0 && (
              <div className="flex flex-col items-center justify-center h-48 text-center">
                <svg width="32" height="32" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-stone-300 dark:text-stone-600 mb-2">
                  <rect x="2" y="3" width="12" height="2" rx="0.5" />
                  <path d="M3 5v7.5a1.5 1.5 0 001.5 1.5h7a1.5 1.5 0 001.5-1.5V5" />
                  <path d="M6.5 8h3" strokeLinecap="round" />
                </svg>
                <p className="text-sm text-stone-400 dark:text-stone-500">No archived goals.</p>
              </div>
            )}

            {activeGoals.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-[10px] font-semibold text-stone-400 dark:text-stone-500 uppercase tracking-widest px-1 pt-1">
                  Active
                </p>
                {activeGoals.map(goal => (
                  <GoalCard
                    key={goal.id}
                    goal={goal}
                    isSelected={selectedGoalId === goal.id}
                    onClick={() => setSelectedGoalId(goal.id)}
                    onUnarchive={() => unarchiveGoal.mutate(goal.id)}
                  />
                ))}
              </div>
            )}

            {completedGoals.length > 0 && (
              <div className="space-y-1.5 mt-3">
                <p className="text-[10px] font-semibold text-stone-400 dark:text-stone-500 uppercase tracking-widest px-1 pt-1">
                  Completed
                </p>
                {completedGoals.map(goal => (
                  <GoalCard
                    key={goal.id}
                    goal={goal}
                    isSelected={selectedGoalId === goal.id}
                    onClick={() => setSelectedGoalId(goal.id)}
                    onUnarchive={() => unarchiveGoal.mutate(goal.id)}
                  />
                ))}
              </div>
            )}

            {selectedGoalId !== null && (
              <div className="mt-4">
                <GoalDetail
                  key={selectedGoalId}
                  goalId={selectedGoalId}
                  readOnly
                  onUnarchive={handleUnarchive}
                />
              </div>
            )}
          </div>
        </div>
        <BottomTabBar />
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-stone-25 dark:bg-stone-900">
      <Sidebar />

      {/* Left panel */}
      <div className="w-72 flex-shrink-0 flex flex-col border-r border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-850 overflow-hidden">
        {/* Panel header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-stone-200 dark:border-stone-700 flex-shrink-0">
          <h1 className="text-base font-semibold text-stone-800 dark:text-stone-100">Archive</h1>
          <Link
            to="/goals"
            className="text-xs text-stone-400 hover:text-stone-600 dark:hover:text-stone-300 transition-colors"
          >
            Back to Goals
          </Link>
        </div>

        {/* Archived goal list */}
        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-1.5">
          {goals.length === 0 && (
            <div className="flex flex-col items-center justify-center h-48 text-center">
              <svg width="32" height="32" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-stone-300 dark:text-stone-600 mb-2">
                <rect x="2" y="3" width="12" height="2" rx="0.5" />
                <path d="M3 5v7.5a1.5 1.5 0 001.5 1.5h7a1.5 1.5 0 001.5-1.5V5" />
                <path d="M6.5 8h3" strokeLinecap="round" />
              </svg>
              <p className="text-sm text-stone-400 dark:text-stone-500">No archived goals.</p>
            </div>
          )}

          {activeGoals.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-[10px] font-semibold text-stone-400 dark:text-stone-500 uppercase tracking-widest px-1 pt-1">
                Active
              </p>
              {activeGoals.map(goal => (
                <GoalCard
                  key={goal.id}
                  goal={goal}
                  isSelected={selectedGoalId === goal.id}
                  onClick={() => setSelectedGoalId(goal.id)}
                  onUnarchive={() => unarchiveGoal.mutate(goal.id)}
                />
              ))}
            </div>
          )}

          {completedGoals.length > 0 && (
            <div className="space-y-1.5 mt-3">
              <p className="text-[10px] font-semibold text-stone-400 dark:text-stone-500 uppercase tracking-widest px-1 pt-1">
                Completed
              </p>
              {completedGoals.map(goal => (
                <GoalCard
                  key={goal.id}
                  goal={goal}
                  isSelected={selectedGoalId === goal.id}
                  onClick={() => setSelectedGoalId(goal.id)}
                  onUnarchive={() => unarchiveGoal.mutate(goal.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {selectedGoalId !== null ? (
          <GoalDetail
            key={selectedGoalId}
            goalId={selectedGoalId}
            readOnly
            onUnarchive={handleUnarchive}
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
            <svg width="48" height="48" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1" className="text-stone-300 dark:text-stone-600 mb-4">
              <rect x="2" y="3" width="12" height="2" rx="0.5" />
              <path d="M3 5v7.5a1.5 1.5 0 001.5 1.5h7a1.5 1.5 0 001.5-1.5V5" />
              <path d="M6.5 8h3" strokeLinecap="round" />
            </svg>
            <p className="text-base font-medium text-stone-400 dark:text-stone-500">
              {goals.length === 0 ? 'No archived goals' : 'Select an archived goal'}
            </p>
            <p className="text-sm text-stone-300 dark:text-stone-600 mt-1">
              {goals.length === 0
                ? 'Goals you archive will appear here.'
                : 'Click a goal on the left to view it.'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
