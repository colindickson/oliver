import { useState } from 'react'
import { Sidebar } from '../components/Sidebar'
import { GoalCard } from '../components/GoalCard'
import { GoalDetail } from '../components/GoalDetail'
import { useGoals } from '../hooks/useGoals'

function NewGoalForm({ onCreate, onCancel }: { onCreate: (title: string) => void; onCancel: () => void }) {
  const [title, setTitle] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = title.trim()
    if (trimmed) onCreate(trimmed)
  }

  return (
    <form onSubmit={handleSubmit} className="mx-1 mb-2">
      <input
        autoFocus
        type="text"
        value={title}
        onChange={e => setTitle(e.target.value)}
        onKeyDown={e => { if (e.key === 'Escape') onCancel() }}
        placeholder="Goal title…"
        className="w-full text-sm px-3 py-2 rounded-lg border border-terracotta-300 dark:border-terracotta-600 bg-white dark:bg-stone-800 text-stone-800 dark:text-stone-100 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-terracotta-300 dark:focus:ring-terracotta-600"
      />
      <div className="flex gap-2 mt-2">
        <button
          type="submit"
          disabled={!title.trim()}
          className="flex-1 text-xs font-medium py-1.5 rounded-lg bg-terracotta-500 hover:bg-terracotta-600 text-white transition-colors disabled:opacity-40"
        >
          Create
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="text-xs py-1.5 px-3 rounded-lg text-stone-500 hover:bg-stone-100 dark:hover:bg-stone-700 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

export function Goals() {
  const { goals, createGoal, deleteGoal } = useGoals()
  const [selectedGoalId, setSelectedGoalId] = useState<number | null>(null)
  const [showNewForm, setShowNewForm] = useState(false)

  const activeGoals = goals.filter(g => g.status === 'active')
  const completedGoals = goals.filter(g => g.status === 'completed')

  function handleCreate(title: string) {
    createGoal.mutate({ title }, {
      onSuccess: (newGoal) => {
        setSelectedGoalId(newGoal.id)
        setShowNewForm(false)
      },
    })
  }

  function handleDeleted() {
    if (selectedGoalId !== null) {
      deleteGoal.mutate(selectedGoalId, {
        onSuccess: () => setSelectedGoalId(null),
      })
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-stone-25 dark:bg-stone-900">
      <Sidebar />

      {/* Left panel */}
      <div className="w-72 flex-shrink-0 flex flex-col border-r border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-850 overflow-hidden">
        {/* Panel header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-stone-200 dark:border-stone-700 flex-shrink-0">
          <h1 className="text-base font-semibold text-stone-800 dark:text-stone-100">Goals</h1>
          <button
            onClick={() => { setShowNewForm(true) }}
            className="flex items-center gap-1 text-xs font-medium text-terracotta-500 hover:text-terracotta-600 dark:text-terracotta-400 dark:hover:text-terracotta-300 transition-colors"
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 2v8M2 6h8" strokeLinecap="round" />
            </svg>
            New Goal
          </button>
        </div>

        {/* Goal list */}
        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-1.5">
          {showNewForm && (
            <NewGoalForm onCreate={handleCreate} onCancel={() => setShowNewForm(false)} />
          )}

          {goals.length === 0 && !showNewForm && (
            <div className="flex flex-col items-center justify-center h-48 text-center">
              <p className="text-sm text-stone-400 dark:text-stone-500">No goals yet.</p>
              <button
                onClick={() => setShowNewForm(true)}
                className="mt-2 text-xs text-terracotta-500 dark:text-terracotta-400 hover:underline"
              >
                Create your first goal
              </button>
            </div>
          )}

          {/* Active */}
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
                />
              ))}
            </div>
          )}

          {/* Completed */}
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
            onDeleted={handleDeleted}
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-stone-300 dark:text-stone-600 mb-4">
              <circle cx="24" cy="24" r="20" />
              <circle cx="24" cy="24" r="10" />
              <circle cx="24" cy="24" r="3" fill="currentColor" stroke="none" />
              <path d="M24 4v4M24 40v4M4 24h4M40 24h4" strokeLinecap="round" />
            </svg>
            <p className="text-base font-medium text-stone-400 dark:text-stone-500">
              {goals.length === 0 ? 'Create your first goal' : 'Select a goal'}
            </p>
            <p className="text-sm text-stone-300 dark:text-stone-600 mt-1">
              {goals.length === 0
                ? 'Goals help you track long-term objectives across many tasks.'
                : 'Click a goal on the left to view and edit it.'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
