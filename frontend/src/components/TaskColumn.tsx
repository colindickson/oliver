import { useState } from 'react'
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
  arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import type { Task } from '../api/client'
import { TaskCard } from './TaskCard'
import { TagInput } from './TagInput'

type ColorKey = 'blue' | 'amber' | 'green'

interface Props {
  title: string
  category: Task['category']
  tasks: Task[]
  colorClass: ColorKey
  onAddTask: (title: string, description: string, tags: string[]) => Promise<void>
  onComplete: (task: Task) => void
  onDelete: (id: number) => void
  onReorder: (taskIds: number[]) => void
  onMoveToBacklog?: (task: Task) => void
}

const headerColors: Record<ColorKey, string> = {
  blue: 'border-ocean-400 text-ocean-700 dark:text-ocean-400',
  amber: 'border-terracotta-400 text-terracotta-700 dark:text-terracotta-400',
  green: 'border-moss-400 text-moss-700 dark:text-moss-400',
}

const buttonColors: Record<ColorKey, string> = {
  blue: 'bg-ocean-50 text-ocean-600 hover:bg-ocean-100 border-ocean-200 dark:bg-ocean-900/20 dark:text-ocean-300 dark:hover:bg-ocean-900/30 dark:border-ocean-800/30',
  amber: 'bg-terracotta-50 text-terracotta-600 hover:bg-terracotta-100 border-terracotta-200 dark:bg-terracotta-900/20 dark:text-terracotta-300 dark:hover:bg-terracotta-900/30 dark:border-terracotta-800/30',
  green: 'bg-moss-50 text-moss-600 hover:bg-moss-100 border-moss-200 dark:bg-moss-900/20 dark:text-moss-300 dark:hover:bg-moss-900/30 dark:border-moss-800/30',
}

interface SortableTaskCardProps {
  task: Task
  onComplete: (task: Task) => void
  onDelete: (id: number) => void
  onMoveToBacklog?: (task: Task) => void
}

function SortableTaskCard({ task, onComplete, onDelete, onMoveToBacklog }: SortableTaskCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: task.id })

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div ref={setNodeRef} style={style} className="flex items-start gap-1">
      {/* Drag handle */}
      <button
        type="button"
        className="mt-3 flex-shrink-0 text-stone-200 hover:text-stone-400 cursor-grab active:cursor-grabbing transition-colors px-0.5 dark:text-stone-600 dark:hover:text-stone-400"
        aria-label="Drag to reorder"
        {...attributes}
        {...listeners}
      >
        <svg width="10" height="16" viewBox="0 0 10 16" fill="currentColor">
          <circle cx="3" cy="3" r="1.5" />
          <circle cx="7" cy="3" r="1.5" />
          <circle cx="3" cy="8" r="1.5" />
          <circle cx="7" cy="8" r="1.5" />
          <circle cx="3" cy="13" r="1.5" />
          <circle cx="7" cy="13" r="1.5" />
        </svg>
      </button>
      <div className="flex-1 min-w-0">
        <TaskCard task={task} onComplete={onComplete} onDelete={onDelete} onMoveToBacklog={onMoveToBacklog} />
      </div>
    </div>
  )
}

export function TaskColumn({
  title,
  category,
  tasks,
  colorClass,
  onAddTask,
  onComplete,
  onDelete,
  onReorder,
  onMoveToBacklog,
}: Props) {
  const [adding, setAdding] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [newTags, setNewTags] = useState<string[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Maintain local ordered list
  const initialCategoryTasks = tasks
    .filter(t => t.category === category)
    .sort((a, b) => a.order_index - b.order_index)
  const [orderedTasks, setOrderedTasks] = useState<Task[]>(initialCategoryTasks)

  // Sync with server updates
  const incomingIds = initialCategoryTasks.map(t => t.id).join(',')
  const localIds = orderedTasks.map(t => t.id).join(',')
  const syncedTasks =
    incomingIds === localIds
      ? orderedTasks.map(ot => initialCategoryTasks.find(t => t.id === ot.id) ?? ot)
      : initialCategoryTasks

  const completedCount = syncedTasks.filter(t => t.status === 'completed').length

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  )

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return

    const oldIndex = syncedTasks.findIndex(t => t.id === active.id)
    const newIndex = syncedTasks.findIndex(t => t.id === over.id)
    if (oldIndex === -1 || newIndex === -1) return

    const reordered = arrayMove(syncedTasks, oldIndex, newIndex)
    setOrderedTasks(reordered)
    onReorder(reordered.map(t => t.id))
  }

  async function handleAdd() {
    if (!newTitle.trim()) return
    setIsSubmitting(true)
    try {
      await onAddTask(newTitle.trim(), newDesc.trim(), newTags)
      setNewTitle('')
      setNewDesc('')
      setNewTags([])
      setAdding(false)
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      void handleAdd()
    }
    if (e.key === 'Escape') {
      setAdding(false)
      setNewTitle('')
      setNewDesc('')
      setNewTags([])
    }
  }

  function handleCancel() {
    setAdding(false)
    setNewTitle('')
    setNewDesc('')
    setNewTags([])
  }

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-white dark:bg-stone-700 dark:border-stone-600/30 rounded-2xl border border-stone-100 shadow-soft p-5">
      {/* Column header */}
      <div
        className={`flex items-center justify-between mb-4 pb-3 border-b-2 ${headerColors[colorClass]}`}
      >
        <h2 className="font-semibold text-sm uppercase tracking-wide">{title}</h2>
        <span className="text-xs text-stone-400 tabular-nums">
          {completedCount}/{syncedTasks.length}
        </span>
      </div>

      {/* Task list with drag-to-reorder */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={syncedTasks.map(t => t.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="flex flex-col gap-2 flex-1 overflow-auto">
            {syncedTasks.map(task => (
              <SortableTaskCard
                key={task.id}
                task={task}
                onComplete={onComplete}
                onDelete={onDelete}
                onMoveToBacklog={onMoveToBacklog}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      {/* Add task area */}
      {adding ? (
        <div className="mt-4 space-y-2 animate-fade-in">
          <input
            autoFocus
            type="text"
            value={newTitle}
            onChange={e => setNewTitle(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Task title"
            className="w-full text-sm border border-stone-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent transition-shadow dark:bg-stone-800 dark:border-stone-600 dark:text-stone-100"
          />
          <input
            type="text"
            value={newDesc}
            onChange={e => setNewDesc(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Escape') handleCancel()
            }}
            placeholder="Description (optional)"
            className="w-full text-sm border border-stone-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent transition-shadow dark:bg-stone-800 dark:border-stone-600 dark:text-stone-100"
          />
          <TagInput value={newTags} onChange={setNewTags} />
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={() => void handleAdd()}
              disabled={isSubmitting || !newTitle.trim()}
              className="text-sm bg-stone-800 text-white rounded-lg px-4 py-2 hover:bg-stone-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all dark:bg-stone-600 dark:hover:bg-stone-500"
            >
              Add
            </button>
            <button
              type="button"
              onClick={handleCancel}
              className="text-sm text-stone-400 hover:text-stone-600 transition-colors px-2 dark:text-stone-500 dark:hover:text-stone-300"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          data-add-task
          onClick={() => setAdding(true)}
          className={`mt-4 w-full text-sm border rounded-lg py-2.5 transition-all ${buttonColors[colorClass]}`}
        >
          + Add task
        </button>
      )}
    </div>
  )
}
