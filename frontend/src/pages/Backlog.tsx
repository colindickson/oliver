import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { backlogApi, dayApi, taskApi, tagApi, type Task, type TagResponse } from '../api/client'
import { Sidebar } from '../components/Sidebar'
import { NotificationBanner } from '../components/NotificationBanner'
import { TagInput } from '../components/TagInput'
import { ConfirmableDelete } from '../components/ConfirmableDelete'

// Category badge colors
const categoryColors: Record<string, string> = {
  deep_work: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  short_task: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  maintenance: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
}

const categoryLabels: Record<string, string> = {
  deep_work: 'Deep Work',
  short_task: 'Short Task',
  maintenance: 'Maintenance',
}

// BacklogTaskCard component
interface BacklogTaskCardProps {
  task: Task
  onEdit: (id: number, title: string, description: string, tags: string[]) => void
  onMoveToDay: (task: Task) => void
  onDelete: (id: number) => void
}

function BacklogTaskCard({ task, onEdit, onMoveToDay, onDelete }: BacklogTaskCardProps) {
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(task.title)
  const [editDescription, setEditDescription] = useState(task.description ?? '')
  const [editTags, setEditTags] = useState<string[]>(task.tags ?? [])

  function openEdit() {
    setEditTitle(task.title)
    setEditDescription(task.description ?? '')
    setEditTags(task.tags ?? [])
    setEditing(true)
  }

  function cancelEdit() {
    setEditing(false)
  }

  function saveEdit() {
    if (!editTitle.trim()) return
    onEdit(task.id, editTitle.trim(), editDescription.trim(), editTags)
    setEditing(false)
  }

  if (editing) {
    return (
      <div className="p-3 rounded-xl border border-terracotta-200 bg-white dark:bg-stone-800 dark:border-terracotta-700/40 shadow-sm space-y-2">
        <input
          autoFocus
          type="text"
          value={editTitle}
          onChange={e => setEditTitle(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') saveEdit()
            if (e.key === 'Escape') cancelEdit()
          }}
          className="w-full text-sm border border-stone-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent dark:bg-stone-700 dark:border-stone-600 dark:text-stone-100"
        />
        <textarea
          value={editDescription}
          onChange={e => setEditDescription(e.target.value)}
          placeholder="Description (optional)"
          rows={2}
          className="w-full text-sm border border-stone-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent resize-none dark:bg-stone-700 dark:border-stone-600 dark:text-stone-100 dark:placeholder-stone-400"
        />
        <TagInput value={editTags} onChange={setEditTags} />
        <div className="flex gap-2 pt-0.5">
          <button
            type="button"
            onClick={saveEdit}
            disabled={!editTitle.trim()}
            className="text-xs bg-stone-800 text-white rounded-lg px-3 py-1.5 hover:bg-stone-700 disabled:opacity-50 transition-all dark:bg-stone-600 dark:hover:bg-stone-500"
          >
            Save
          </button>
          <button
            type="button"
            onClick={cancelEdit}
            className="text-xs text-stone-400 hover:text-stone-600 transition-colors px-2 dark:text-stone-500 dark:hover:text-stone-300"
          >
            Cancel
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="group p-3 rounded-xl border border-stone-100 bg-white dark:bg-stone-800 dark:border-stone-700/60 shadow-sm flex items-start gap-3 transition-all duration-200 hover:shadow-soft">
      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-stone-800 dark:text-stone-100">
          {task.title}
        </p>
        {task.description && (
          <p className="text-xs text-stone-400 mt-0.5 truncate">{task.description}</p>
        )}
        <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
          {/* Category badge */}
          {task.category && (
            <span className={`text-xs px-2 py-0.5 rounded-full ${categoryColors[task.category]}`}>
              {categoryLabels[task.category]}
            </span>
          )}
          {/* Tags */}
          {task.tags.map(tag => (
            <span
              key={tag}
              className="text-xs px-1.5 py-0.5 rounded-full bg-stone-100 text-stone-500 dark:bg-stone-700 dark:text-stone-400"
            >
              #{tag}
            </span>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 flex-shrink-0">
        {/* Edit */}
        <button
          type="button"
          onClick={openEdit}
          className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-stone-500 hover:bg-stone-50 rounded transition-colors opacity-0 group-hover:opacity-100 dark:text-stone-600 dark:hover:text-stone-300 dark:hover:bg-stone-700"
          aria-label="Edit task"
        >
          <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M9 2L11 4L5 10H3V8L9 2Z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        {/* Move to Day */}
        <button
          type="button"
          onClick={() => onMoveToDay(task)}
          className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-moss-500 hover:bg-moss-50 rounded transition-colors dark:text-stone-600 dark:hover:text-moss-400 dark:hover:bg-stone-700"
          aria-label="Move to day"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="1" y="2" width="12" height="11" rx="1.5" />
            <path d="M1 6h12" />
            <path d="M4 1v2M10 1v2" />
          </svg>
        </button>

        {/* Delete */}
        <ConfirmableDelete onConfirm={() => onDelete(task.id)} />
      </div>
    </div>
  )
}

// MoveToDayModal component
interface MoveToDayModalProps {
  task: Task
  onClose: () => void
  onMove: (taskId: number, dayId: number, category: 'deep_work' | 'short_task' | 'maintenance') => void
}

function MoveToDayModal({ task, onClose, onMove }: MoveToDayModalProps) {
  const [selectedDay, setSelectedDay] = useState<string>('today')
  const [selectedCategory, setSelectedCategory] = useState<'deep_work' | 'short_task' | 'maintenance'>(task.category ?? 'short_task')

  const { data: days = [] } = useQuery({
    queryKey: ['days', 'all'],
    queryFn: dayApi.getAll,
  })

  // Get today's date string
  const todayStr = new Date().toISOString().slice(0, 10)

  // Build list of recent days (last 7 days + next 7 days)
  const recentDays = useMemo(() => {
    const result: Array<{ date: string; label: string }> = [
      { date: todayStr, label: 'Today' },
    ]
    // Add next 6 days
    for (let i = 1; i <= 6; i++) {
      const d = new Date()
      d.setDate(d.getDate() + i)
      const dateStr = d.toISOString().slice(0, 10)
      result.push({
        date: dateStr,
        label: d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
      })
    }
    return result
  }, [todayStr])

  function handleMove() {
    const dayId = days.find(d => d.date === selectedDay)?.id
    if (!dayId) return
    onMove(task.id, dayId, selectedCategory)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 dark:bg-black/50">
      <div className="bg-white rounded-2xl shadow-soft-lg max-w-md w-full mx-4 overflow-hidden dark:bg-stone-800">
        {/* Header */}
        <div className="px-5 py-4 border-b border-stone-100 dark:border-stone-700">
          <h3 className="text-base font-semibold text-stone-800 dark:text-stone-100">Move to Day</h3>
          <p className="text-xs text-stone-400 mt-0.5">{task.title}</p>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4">
          {/* Day selector */}
          <div>
            <label className="block text-xs font-medium text-stone-600 mb-2 dark:text-stone-300">Select Day</label>
            <select
              value={selectedDay}
              onChange={e => setSelectedDay(e.target.value)}
              className="w-full text-sm border border-stone-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent dark:bg-stone-700 dark:border-stone-600 dark:text-stone-100"
            >
              {recentDays.map(d => (
                <option key={d.date} value={d.date}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>

          {/* Category selector */}
          <div>
            <label className="block text-xs font-medium text-stone-600 mb-2 dark:text-stone-300">Category</label>
            <div className="flex gap-2">
              {(['deep_work', 'short_task', 'maintenance'] as const).map(cat => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setSelectedCategory(cat)}
                  className={`flex-1 px-3 py-2 text-xs font-medium rounded-lg border transition-all ${
                    selectedCategory === cat
                      ? 'border-terracotta-300 bg-terracotta-50 text-terracotta-700 dark:border-terracotta-600 dark:bg-terracotta-900/30 dark:text-terracotta-300'
                      : 'border-stone-200 text-stone-600 hover:bg-stone-50 dark:border-stone-600 dark:text-stone-300 dark:hover:bg-stone-700'
                  }`}
                >
                  {categoryLabels[cat]}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-stone-100 flex justify-end gap-2 dark:border-stone-700">
          <button
            type="button"
            onClick={onClose}
            className="text-xs text-stone-400 hover:text-stone-600 transition-colors px-3 py-1.5 dark:text-stone-500 dark:hover:text-stone-300"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleMove}
            className="text-xs bg-terracotta-500 text-white rounded-lg px-4 py-1.5 hover:bg-terracotta-600 transition-all"
          >
            Move Task
          </button>
        </div>
      </div>
    </div>
  )
}

// AddTaskForm component
interface AddTaskFormProps {
  onAdd: (title: string, description: string, tags: string[]) => void
  isLoading: boolean
}

function AddTaskForm({ onAdd, isLoading }: AddTaskFormProps) {
  const [expanded, setExpanded] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState<string[]>([])

  function handleSubmit() {
    if (!title.trim()) return
    onAdd(title.trim(), description.trim(), tags)
    setTitle('')
    setDescription('')
    setTags([])
    setExpanded(false)
  }

  function handleCancel() {
    setTitle('')
    setDescription('')
    setTags([])
    setExpanded(false)
  }

  if (!expanded) {
    return (
      <button
        type="button"
        data-add-task
        onClick={() => setExpanded(true)}
        className="w-full p-3 rounded-xl border-2 border-dashed border-stone-200 text-sm text-stone-400 hover:border-terracotta-300 hover:text-terracotta-500 transition-all flex items-center justify-center gap-2 dark:border-stone-600 dark:hover:border-terracotta-500 dark:text-stone-500 dark:hover:text-terracotta-400"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M7 2v10M2 7h10" strokeLinecap="round" />
        </svg>
        Add task to backlog
      </button>
    )
  }

  return (
    <div className="p-3 rounded-xl border border-terracotta-200 bg-white dark:bg-stone-800 dark:border-terracotta-700/40 shadow-sm space-y-2">
      <input
        autoFocus
        type="text"
        value={title}
        onChange={e => setTitle(e.target.value)}
        onKeyDown={e => {
          if (e.key === 'Enter') handleSubmit()
          if (e.key === 'Escape') handleCancel()
        }}
        placeholder="Task title..."
        className="w-full text-sm border border-stone-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent dark:bg-stone-700 dark:border-stone-600 dark:text-stone-100 dark:placeholder-stone-400"
      />
      <textarea
        value={description}
        onChange={e => setDescription(e.target.value)}
        placeholder="Description (optional)"
        rows={2}
        className="w-full text-sm border border-stone-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent resize-none dark:bg-stone-700 dark:border-stone-600 dark:text-stone-100 dark:placeholder-stone-400"
      />
      <TagInput value={tags} onChange={setTags} />
      <div className="flex gap-2 pt-0.5">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isLoading || !title.trim()}
          className="text-xs bg-stone-800 text-white rounded-lg px-3 py-1.5 hover:bg-stone-700 disabled:opacity-50 transition-all dark:bg-stone-600 dark:hover:bg-stone-500"
        >
          Add to Backlog
        </button>
        <button
          type="button"
          onClick={handleCancel}
          className="text-xs text-stone-400 hover:text-stone-600 transition-colors px-2 dark:text-stone-500 dark:hover:text-stone-300"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}

// Main Backlog page
export function Backlog() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [selectedTag, setSelectedTag] = useState<string | null>(null)
  const [moveTask, setMoveTask] = useState<Task | null>(null)

  // Fetch backlog tasks
  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['backlog', selectedTag, search],
    queryFn: () => backlogApi.list({ tag: selectedTag ?? undefined, search: search || undefined }),
  })

  // Fetch all tags for filter chips
  const { data: allTags = [] } = useQuery<TagResponse[]>({
    queryKey: ['tags', 'all'],
    queryFn: tagApi.getAll,
  })

  // Create backlog task
  const createTask = useMutation({
    mutationFn: (payload: { title: string; description?: string; tags?: string[] }) =>
      backlogApi.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['backlog'] }),
  })

  // Update task
  const updateTask = useMutation({
    mutationFn: ({ id, title, description, tags }: { id: number; title: string; description: string; tags: string[] }) =>
      taskApi.update(id, { title, description: description || null, tags }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['backlog'] })
      qc.invalidateQueries({ queryKey: ['tags'] })
    },
  })

  // Move to day
  const moveToDay = useMutation({
    mutationFn: ({ taskId, dayId, category }: { taskId: number; dayId: number; category: 'deep_work' | 'short_task' | 'maintenance' }) =>
      backlogApi.moveToDay(taskId, { day_id: dayId, category }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['backlog'] })
      qc.invalidateQueries({ queryKey: ['day'] })
    },
  })

  // Delete task
  const deleteTask = useMutation({
    mutationFn: taskApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['backlog'] }),
  })

  function handleAddTask(title: string, description: string, tags: string[]) {
    createTask.mutate({
      title,
      description: description || undefined,
      tags: tags.length > 0 ? tags : undefined,
    })
  }

  function handleEditTask(id: number, title: string, description: string, tags: string[]) {
    updateTask.mutate({ id, title, description, tags })
  }

  function handleMoveToDay(taskId: number, dayId: number, category: 'deep_work' | 'short_task' | 'maintenance') {
    moveToDay.mutate({ taskId, dayId, category })
  }

  function handleDelete(id: number) {
    deleteTask.mutate(id)
  }

  // Filter tags to only show those that are used in backlog
  const backlogTagSet = new Set(tasks.flatMap(t => t.tags))
  const relevantTags = allTags.filter(t => backlogTagSet.has(t.name))

  return (
    <div className="flex min-h-screen bg-stone-25 dark:bg-stone-800">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-stone-200 px-8 py-5 flex items-center justify-between flex-shrink-0 dark:bg-stone-800/90 dark:border-stone-700/50">
          <div>
            <h1 className="text-xl font-semibold text-stone-800 dark:text-stone-100">Backlog</h1>
            <p className="text-sm text-stone-400 mt-0.5">
              {tasks.length} task{tasks.length !== 1 ? 's' : ''} waiting to be scheduled
            </p>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-8 overflow-auto">
          <div className="max-w-2xl space-y-6">
            {/* Search and filters */}
            <div className="space-y-3">
              {/* Search input */}
              <div className="relative">
                <svg
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-stone-400"
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                >
                  <circle cx="6" cy="6" r="4" />
                  <path d="M10 10L13 13" strokeLinecap="round" />
                </svg>
                <input
                  type="text"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Search backlog..."
                  className="w-full text-sm border border-stone-200 rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent dark:bg-stone-700 dark:border-stone-600 dark:text-stone-100 dark:placeholder-stone-400"
                />
                {search && (
                  <button
                    type="button"
                    onClick={() => setSearch('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600 dark:hover:text-stone-300"
                  >
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M2 2L10 10M10 2L2 10" strokeLinecap="round" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Tag filter chips */}
              {relevantTags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => setSelectedTag(null)}
                    className={`text-xs px-3 py-1 rounded-full border transition-all ${
                      selectedTag === null
                        ? 'bg-terracotta-50 border-terracotta-200 text-terracotta-700 dark:bg-terracotta-900/30 dark:border-terracotta-700/30 dark:text-terracotta-300'
                        : 'border-stone-200 text-stone-500 hover:bg-stone-50 dark:border-stone-600 dark:text-stone-400 dark:hover:bg-stone-700'
                    }`}
                  >
                    All
                  </button>
                  {relevantTags.map(tag => (
                    <button
                      key={tag.name}
                      type="button"
                      onClick={() => setSelectedTag(selectedTag === tag.name ? null : tag.name)}
                      className={`text-xs px-3 py-1 rounded-full border transition-all ${
                        selectedTag === tag.name
                          ? 'bg-terracotta-50 border-terracotta-200 text-terracotta-700 dark:bg-terracotta-900/30 dark:border-terracotta-700/30 dark:text-terracotta-300'
                          : 'border-stone-200 text-stone-500 hover:bg-stone-50 dark:border-stone-600 dark:text-stone-400 dark:hover:bg-stone-700'
                      }`}
                    >
                      #{tag.name}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Add task form */}
            <AddTaskForm onAdd={handleAddTask} isLoading={createTask.isPending} />

            {/* Task list */}
            {isLoading ? (
              <div className="text-center py-8 text-stone-400 text-sm">Loading...</div>
            ) : tasks.length === 0 ? (
              <div className="text-center py-8 text-stone-400 text-sm">
                {search || selectedTag
                  ? 'No tasks match your filters'
                  : 'Your backlog is empty. Add tasks above.'}
              </div>
            ) : (
              <div className="space-y-2">
                {tasks.map(task => (
                  <BacklogTaskCard
                    key={task.id}
                    task={task}
                    onEdit={handleEditTask}
                    onMoveToDay={setMoveTask}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Move to Day Modal */}
      {moveTask && (
        <MoveToDayModal
          task={moveTask}
          onClose={() => setMoveTask(null)}
          onMove={handleMoveToDay}
        />
      )}

      {/* Notification banner */}
      <NotificationBanner />
    </div>
  )
}
