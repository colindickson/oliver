import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { backlogApi, taskApi, dayApi, type Task } from '../api/client'

interface Props {
  linkedTaskIds: number[]
  onClose: () => void
  onSave: (taskIds: number[]) => void
}

export function GoalTaskPicker({ linkedTaskIds, onClose, onSave }: Props) {
  const [selected, setSelected] = useState<Set<number>>(new Set(linkedTaskIds))
  const [search, setSearch] = useState('')

  const { data: days = [] } = useQuery({
    queryKey: ['days', 'all'],
    queryFn: dayApi.getAll,
  })

  const { data: backlog = [] } = useQuery({
    queryKey: ['backlog'],
    queryFn: () => backlogApi.list(),
  })

  // Flatten all tasks across all days + backlog
  const allTasks: (Task & { dayDate?: string })[] = [
    ...days.flatMap(d => d.tasks.map(t => ({ ...t, dayDate: d.date }))),
    ...backlog.map(t => ({ ...t, dayDate: undefined })),
  ]

  // Deduplicate by id
  const seen = new Set<number>()
  const uniqueTasks = allTasks.filter(t => {
    if (seen.has(t.id)) return false
    seen.add(t.id)
    return true
  })

  const filtered = uniqueTasks.filter(t =>
    t.title.toLowerCase().includes(search.toLowerCase())
  )

  function toggle(id: number) {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white dark:bg-stone-800 rounded-2xl shadow-2xl w-full max-w-lg mx-4 flex flex-col max-h-[80vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-stone-200 dark:border-stone-700">
          <h2 className="text-sm font-semibold text-stone-800 dark:text-stone-100">Link Tasks</h2>
          <button
            onClick={onClose}
            className="text-stone-400 hover:text-stone-600 dark:hover:text-stone-200 transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 3l10 10M13 3L3 13" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        {/* Search */}
        <div className="px-4 py-3 border-b border-stone-100 dark:border-stone-700">
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search tasks…"
            autoFocus
            className="w-full text-sm px-3 py-2 rounded-lg border border-stone-200 dark:border-stone-600 bg-stone-50 dark:bg-stone-700 text-stone-800 dark:text-stone-100 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-terracotta-300 dark:focus:ring-terracotta-600"
          />
        </div>

        {/* Task list */}
        <div className="flex-1 overflow-y-auto py-2">
          {filtered.length === 0 && (
            <p className="text-center text-sm text-stone-400 dark:text-stone-500 py-8">
              No tasks found.
            </p>
          )}
          {filtered.map(task => {
            const isChecked = selected.has(task.id)
            return (
              <button
                key={task.id}
                onClick={() => toggle(task.id)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                  isChecked
                    ? 'bg-terracotta-50 dark:bg-terracotta-900/20'
                    : 'hover:bg-stone-50 dark:hover:bg-stone-700/50'
                }`}
              >
                {/* Checkbox */}
                <span className={`flex-shrink-0 w-4 h-4 rounded border-2 flex items-center justify-center transition-colors ${
                  isChecked
                    ? 'bg-terracotta-500 border-terracotta-500'
                    : 'border-stone-300 dark:border-stone-600'
                }`}>
                  {isChecked && (
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="white" strokeWidth="2">
                      <path d="M1.5 5l2.5 2.5 4.5-4.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </span>

                {/* Task info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-stone-700 dark:text-stone-200 truncate">{task.title}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    {task.dayDate && (
                      <span className="text-[11px] text-stone-400 dark:text-stone-500">{task.dayDate}</span>
                    )}
                    {!task.dayDate && (
                      <span className="text-[11px] text-stone-400 dark:text-stone-500">Backlog</span>
                    )}
                    {task.tags.map(tag => (
                      <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded-full bg-stone-100 dark:bg-stone-700 text-stone-500 dark:text-stone-400">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Status dot */}
                <span className={`flex-shrink-0 w-2 h-2 rounded-full ${
                  task.status === 'completed'
                    ? 'bg-moss-500 dark:bg-moss-400'
                    : task.status === 'in_progress'
                    ? 'bg-amber-400'
                    : 'bg-stone-300 dark:bg-stone-600'
                }`} />
              </button>
            )
          })}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-4 border-t border-stone-200 dark:border-stone-700">
          <span className="text-xs text-stone-400 dark:text-stone-500">
            {selected.size} task{selected.size !== 1 ? 's' : ''} selected
          </span>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="text-sm px-3 py-1.5 rounded-lg text-stone-500 hover:bg-stone-100 dark:hover:bg-stone-700 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={() => onSave(Array.from(selected))}
              className="text-sm px-4 py-1.5 rounded-lg bg-terracotta-500 hover:bg-terracotta-600 text-white font-medium transition-colors"
            >
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
