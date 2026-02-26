import { useState } from 'react'
import type { GoalDetail as GoalDetailType, Task } from '../api/client'
import { TagInput } from './TagInput'
import { GoalTaskPicker } from './GoalTaskPicker'
import { ConfirmableDelete } from './ConfirmableDelete'
import { useGoalDetail } from '../hooks/useGoalDetail'

interface Props {
  goalId: number
  onDeleted: () => void
}

function TaskRow({ task }: { task: Task & { dayDate?: string } }) {
  const statusIcon = {
    completed: (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" className="text-moss-500 dark:text-moss-400">
        <circle cx="7" cy="7" r="6" />
        <path d="M4 7l2.5 2.5 3.5-3.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    in_progress: (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" className="text-amber-400">
        <circle cx="7" cy="7" r="6" />
        <path d="M7 4v3l2 2" strokeLinecap="round" />
      </svg>
    ),
    pending: (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-stone-300 dark:text-stone-600">
        <circle cx="7" cy="7" r="6" />
      </svg>
    ),
  }

  return (
    <div className={`flex items-center gap-2.5 py-2 px-3 rounded-lg ${
      task.status === 'completed'
        ? 'opacity-50'
        : 'hover:bg-stone-50 dark:hover:bg-stone-700/50'
    }`}>
      <span className="flex-shrink-0">{statusIcon[task.status]}</span>
      <span className={`flex-1 text-sm min-w-0 truncate ${
        task.status === 'completed'
          ? 'line-through text-stone-400 dark:text-stone-500'
          : 'text-stone-700 dark:text-stone-200'
      }`}>
        {task.title}
      </span>
      {task.tags.length > 0 && (
        <div className="flex gap-1 flex-shrink-0">
          {task.tags.slice(0, 2).map(tag => (
            <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded-full bg-stone-100 dark:bg-stone-700 text-stone-500 dark:text-stone-400">
              #{tag}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export function GoalDetail({ goalId, onDeleted }: Props) {
  const { goal, updateGoal, setStatus } = useGoalDetail(goalId)
  const [editingTitle, setEditingTitle] = useState(false)
  const [titleDraft, setTitleDraft] = useState('')
  const [editingDesc, setEditingDesc] = useState(false)
  const [descDraft, setDescDraft] = useState('')
  const [showTaskPicker, setShowTaskPicker] = useState(false)

  if (!goal) {
    return (
      <div className="flex-1 flex items-center justify-center text-stone-400 dark:text-stone-500 text-sm">
        Loading…
      </div>
    )
  }

  const remaining = goal.tasks.filter(t => t.status !== 'completed')
  const completed = goal.tasks.filter(t => t.status === 'completed')
  const isOverdue =
    goal.status === 'active' &&
    goal.target_date != null &&
    new Date(goal.target_date) < new Date(new Date().toISOString().slice(0, 10))

  function commitTitle() {
    const trimmed = titleDraft.trim()
    if (trimmed && trimmed !== goal!.title) {
      updateGoal.mutate({ title: trimmed })
    }
    setEditingTitle(false)
  }

  function commitDesc() {
    const trimmed = descDraft.trim()
    if (trimmed !== (goal!.description ?? '')) {
      updateGoal.mutate({ description: trimmed || null })
    }
    setEditingDesc(false)
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header bar */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-stone-200 dark:border-stone-700 flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
            goal.status === 'completed'
              ? 'bg-moss-100 text-moss-700 dark:bg-moss-900/30 dark:text-moss-400'
              : 'bg-terracotta-50 text-terracotta-700 dark:bg-terracotta-900/30 dark:text-terracotta-400'
          }`}>
            {goal.status === 'completed' ? 'Completed' : 'Active'}
          </span>
          {goal.total_tasks > 0 && (
            <span className="text-xs text-stone-400 dark:text-stone-500">
              {goal.completed_tasks}/{goal.total_tasks} tasks · {goal.progress_pct}%
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setStatus.mutate(goal.status === 'completed' ? 'active' : 'completed')}
            disabled={setStatus.isPending}
            className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50 ${
              goal.status === 'completed'
                ? 'bg-stone-100 hover:bg-stone-200 text-stone-600 dark:bg-stone-700 dark:hover:bg-stone-600 dark:text-stone-300'
                : 'bg-moss-500 hover:bg-moss-600 text-white dark:bg-moss-600 dark:hover:bg-moss-500'
            }`}
          >
            {goal.status === 'completed' ? 'Reopen' : 'Mark Complete'}
          </button>
          <ConfirmableDelete
            onConfirm={onDeleted}
            isLoading={false}
          />
        </div>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">

        {/* Title */}
        <div>
          {editingTitle ? (
            <input
              autoFocus
              type="text"
              value={titleDraft}
              onChange={e => setTitleDraft(e.target.value)}
              onBlur={commitTitle}
              onKeyDown={e => {
                if (e.key === 'Enter') commitTitle()
                if (e.key === 'Escape') setEditingTitle(false)
              }}
              className="w-full text-xl font-semibold bg-transparent border-b-2 border-terracotta-400 outline-none text-stone-800 dark:text-stone-100 pb-0.5"
            />
          ) : (
            <h2
              onClick={() => { setTitleDraft(goal.title); setEditingTitle(true) }}
              className="text-xl font-semibold text-stone-800 dark:text-stone-100 cursor-text hover:text-terracotta-600 dark:hover:text-terracotta-400 transition-colors"
            >
              {goal.title}
            </h2>
          )}
        </div>

        {/* Description */}
        <div>
          <label className="text-xs font-medium text-stone-400 dark:text-stone-500 uppercase tracking-wide">
            Description
          </label>
          {editingDesc ? (
            <textarea
              autoFocus
              value={descDraft}
              onChange={e => setDescDraft(e.target.value)}
              onBlur={commitDesc}
              onKeyDown={e => {
                if (e.key === 'Escape') setEditingDesc(false)
              }}
              rows={3}
              className="mt-1 w-full text-sm bg-stone-50 dark:bg-stone-700/50 border border-stone-200 dark:border-stone-600 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-terracotta-300 dark:focus:ring-terracotta-600 text-stone-700 dark:text-stone-200 resize-none"
            />
          ) : (
            <p
              onClick={() => { setDescDraft(goal.description ?? ''); setEditingDesc(true) }}
              className={`mt-1 text-sm cursor-text rounded-lg px-3 py-2 transition-colors hover:bg-stone-50 dark:hover:bg-stone-700/50 ${
                goal.description
                  ? 'text-stone-600 dark:text-stone-300'
                  : 'text-stone-300 dark:text-stone-600 italic'
              }`}
            >
              {goal.description ?? 'Add a description…'}
            </p>
          )}
        </div>

        {/* Target date */}
        <div>
          <label className="text-xs font-medium text-stone-400 dark:text-stone-500 uppercase tracking-wide">
            Target Date
          </label>
          <div className="mt-1 flex items-center gap-2">
            <input
              type="date"
              value={goal.target_date ?? ''}
              onChange={e => updateGoal.mutate({ target_date: e.target.value || 'CLEAR' })}
              className="text-sm px-3 py-1.5 rounded-lg border border-stone-200 dark:border-stone-600 bg-stone-50 dark:bg-stone-700 text-stone-700 dark:text-stone-200 focus:outline-none focus:ring-2 focus:ring-terracotta-300 dark:focus:ring-terracotta-600"
            />
            {isOverdue && (
              <span className="text-xs text-red-500 dark:text-red-400 font-medium">Overdue</span>
            )}
            {goal.target_date && (
              <button
                onClick={() => updateGoal.mutate({ target_date: 'CLEAR' })}
                className="text-xs text-stone-400 hover:text-stone-600 dark:hover:text-stone-200 transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Tags */}
        <div>
          <label className="text-xs font-medium text-stone-400 dark:text-stone-500 uppercase tracking-wide">
            Tags (auto-links tasks)
          </label>
          <div className="mt-1">
            <TagInput
              value={goal.tags}
              onChange={tags => updateGoal.mutate({ tag_names: tags })}
              maxTags={10}
            />
          </div>
        </div>

        {/* Directly linked tasks */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-medium text-stone-400 dark:text-stone-500 uppercase tracking-wide">
              Directly Linked Tasks
            </label>
            <button
              onClick={() => setShowTaskPicker(true)}
              className="text-xs text-terracotta-500 hover:text-terracotta-600 dark:text-terracotta-400 dark:hover:text-terracotta-300 font-medium transition-colors"
            >
              + Link tasks
            </button>
          </div>
          <p className="text-xs text-stone-400 dark:text-stone-500 mb-2">
            These are in addition to tasks pulled in via tags above.
          </p>
        </div>

        {/* Progress bar */}
        {goal.total_tasks > 0 && (
          <div>
            <div className="h-2 bg-stone-100 dark:bg-stone-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  goal.status === 'completed'
                    ? 'bg-moss-500 dark:bg-moss-600'
                    : 'bg-gradient-to-r from-terracotta-400 to-terracotta-500'
                }`}
                style={{ width: `${goal.progress_pct}%` }}
              />
            </div>
          </div>
        )}

        {/* Task list */}
        {goal.tasks.length === 0 && (
          <p className="text-sm text-stone-400 dark:text-stone-500 italic text-center py-4">
            No tasks linked yet. Add tags or link tasks directly.
          </p>
        )}

        {remaining.length > 0 && (
          <div>
            <p className="text-xs font-medium text-stone-400 dark:text-stone-500 uppercase tracking-wide mb-1">
              Remaining ({remaining.length})
            </p>
            {remaining.map(t => <TaskRow key={t.id} task={t} />)}
          </div>
        )}

        {completed.length > 0 && (
          <div>
            <p className="text-xs font-medium text-stone-400 dark:text-stone-500 uppercase tracking-wide mb-1">
              Completed ({completed.length})
            </p>
            {completed.map(t => <TaskRow key={t.id} task={t} />)}
          </div>
        )}
      </div>

      {/* Task picker modal */}
      {showTaskPicker && (
        <GoalTaskPicker
          linkedTaskIds={goal.tasks.map(t => t.id)}
          onClose={() => setShowTaskPicker(false)}
          onSave={ids => {
            updateGoal.mutate({ task_ids: ids })
            setShowTaskPicker(false)
          }}
        />
      )}
    </div>
  )
}
