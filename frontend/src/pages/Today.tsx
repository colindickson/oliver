import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dayApi, taskApi } from '../api/client'
import type { Task } from '../api/client'
import { TaskColumn } from '../components/TaskColumn'
import { Sidebar } from '../components/Sidebar'

interface ColumnConfig {
  title: string
  category: Task['category']
  color: 'blue' | 'amber' | 'green'
}

const columns: ColumnConfig[] = [
  { title: 'Deep Work', category: 'deep_work', color: 'blue' },
  { title: 'Short Tasks', category: 'short_task', color: 'amber' },
  { title: 'Maintenance', category: 'maintenance', color: 'green' },
]

function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  })
}

export function Today() {
  const qc = useQueryClient()

  const { data: day, isLoading } = useQuery({
    queryKey: ['day', 'today'],
    queryFn: dayApi.getToday,
  })

  const createTask = useMutation({
    mutationFn: taskApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['day', 'today'] }),
  })

  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: Task['status'] }) =>
      taskApi.setStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['day', 'today'] }),
  })

  const deleteTask = useMutation({
    mutationFn: taskApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['day', 'today'] }),
  })

  async function handleAddTask(
    category: Task['category'],
    title: string,
    description: string,
  ) {
    if (!day) return
    await createTask.mutateAsync({
      day_id: day.id,
      category,
      title,
      description: description || undefined,
    })
  }

  function handleComplete(task: Task) {
    const next: Task['status'] = task.status === 'completed' ? 'pending' : 'completed'
    setStatus.mutate({ id: task.id, status: next })
  }

  function handleDelete(id: number) {
    deleteTask.mutate(id)
  }

  if (isLoading || !day) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
          Loading...
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between flex-shrink-0">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Today</h1>
            <p className="text-sm text-gray-500 mt-0.5">{formatDate(new Date())}</p>
          </div>
          <div className="text-sm text-gray-400 italic">Timer &middot; Phase 3</div>
        </header>

        {/* Three-column board */}
        <main className="flex-1 p-8">
          <div className="flex gap-8 h-full">
            {columns.map(col => (
              <TaskColumn
                key={col.category}
                title={col.title}
                category={col.category}
                tasks={day.tasks}
                colorClass={col.color}
                onAddTask={(title, desc) => handleAddTask(col.category, title, desc)}
                onComplete={handleComplete}
                onDelete={handleDelete}
              />
            ))}
          </div>
        </main>
      </div>
    </div>
  )
}
