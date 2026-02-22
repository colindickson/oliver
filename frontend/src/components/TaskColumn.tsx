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

type ColorKey = 'blue' | 'amber' | 'green'

interface Props {
  title: string
  category: Task['category']
  tasks: Task[]
  colorClass: ColorKey
  onAddTask: (title: string, description: string) => Promise<void>
  onComplete: (task: Task) => void
  onDelete: (id: number) => void
  onReorder: (taskIds: number[]) => void
}

const headerColors: Record<ColorKey, string> = {
  blue: 'border-blue-400 text-blue-700',
  amber: 'border-amber-400 text-amber-700',
  green: 'border-green-400 text-green-700',
}

const buttonColors: Record<ColorKey, string> = {
  blue: 'bg-blue-50 text-blue-600 hover:bg-blue-100 border-blue-200',
  amber: 'bg-amber-50 text-amber-600 hover:bg-amber-100 border-amber-200',
  green: 'bg-green-50 text-green-600 hover:bg-green-100 border-green-200',
}

interface SortableTaskCardProps {
  task: Task
  onComplete: (task: Task) => void
  onDelete: (id: number) => void
}

function SortableTaskCard({ task, onComplete, onDelete }: SortableTaskCardProps) {
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
        className="mt-3.5 flex-shrink-0 text-gray-200 hover:text-gray-400 cursor-grab active:cursor-grabbing transition-colors px-0.5"
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
        <TaskCard task={task} onComplete={onComplete} onDelete={onDelete} />
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
}: Props) {
  const [adding, setAdding] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Maintain local ordered list so drag feels instant
  const initialCategoryTasks = tasks
    .filter(t => t.category === category)
    .sort((a, b) => a.order_index - b.order_index)
  const [orderedTasks, setOrderedTasks] = useState<Task[]>(initialCategoryTasks)

  // Sync when tasks prop changes from server (e.g. after invalidation)
  // We use a simple comparison: if the set of IDs changed, reset local order
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
      await onAddTask(newTitle.trim(), newDesc.trim())
      setNewTitle('')
      setNewDesc('')
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
    }
  }

  function handleCancel() {
    setAdding(false)
    setNewTitle('')
    setNewDesc('')
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Column header */}
      <div
        className={`flex items-center justify-between mb-4 pb-2 border-b-2 ${headerColors[colorClass]}`}
      >
        <h2 className="font-semibold text-sm uppercase tracking-wide">{title}</h2>
        <span className="text-xs text-gray-400">
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
          <div className="flex flex-col gap-2 flex-1">
            {syncedTasks.map(task => (
              <SortableTaskCard
                key={task.id}
                task={task}
                onComplete={onComplete}
                onDelete={onDelete}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      {/* Add task area */}
      {adding ? (
        <div className="mt-3 space-y-2">
          <input
            autoFocus
            type="text"
            value={newTitle}
            onChange={e => setNewTitle(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Task title"
            className="w-full text-sm border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
          <input
            type="text"
            value={newDesc}
            onChange={e => setNewDesc(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Escape') handleCancel()
            }}
            placeholder="Description (optional)"
            className="w-full text-sm border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => void handleAdd()}
              disabled={isSubmitting || !newTitle.trim()}
              className="text-xs bg-gray-800 text-white rounded px-3 py-1 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
            >
              Add
            </button>
            <button
              type="button"
              onClick={handleCancel}
              className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
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
          className={`mt-3 w-full text-xs border rounded py-1.5 transition-colors ${buttonColors[colorClass]}`}
        >
          + Add task
        </button>
      )}
    </div>
  )
}
