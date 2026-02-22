import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { dayApi } from '../api/client'
import { Sidebar } from '../components/Sidebar'

export function DayDetail() {
  const { date } = useParams<{ date: string }>()
  const navigate = useNavigate()

  const { data: day, isLoading, isError } = useQuery({
    queryKey: ['day', date],
    queryFn: () => dayApi.getByDate(date!),
    enabled: !!date,
  })

  const categories = [
    { key: 'deep_work', label: 'Deep Work', color: 'text-blue-600' },
    { key: 'short_task', label: 'Short Tasks', color: 'text-amber-600' },
    { key: 'maintenance', label: 'Maintenance', color: 'text-green-600' },
  ] as const

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 p-8 max-w-3xl">
        <button onClick={() => navigate('/calendar')} className="text-sm text-gray-400 hover:text-gray-600 mb-6 flex items-center gap-1">
          &larr; Back to Calendar
        </button>

        {isLoading && <p className="text-gray-400">Loading...</p>}
        {isError && <p className="text-red-400">No data for this day.</p>}
        {day && (
          <>
            <h1 className="text-xl font-semibold text-gray-900 mb-6">
              {new Date(day.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
            </h1>

            {categories.map(cat => {
              const tasks = day.tasks.filter(t => t.category === cat.key)
              if (tasks.length === 0) return null
              return (
                <div key={cat.key} className="mb-6">
                  <h2 className={`text-sm font-semibold uppercase tracking-wide mb-2 ${cat.color}`}>{cat.label}</h2>
                  <div className="space-y-2">
                    {tasks.map(task => (
                      <div key={task.id} className="bg-white border rounded-lg p-3 flex items-center gap-3">
                        <div className={`w-4 h-4 rounded-full flex-shrink-0 ${task.status === 'completed' ? 'bg-green-500' : 'bg-gray-200'}`} />
                        <span className={`text-sm ${task.status === 'completed' ? 'line-through text-gray-400' : 'text-gray-800'}`}>
                          {task.title}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </>
        )}
      </div>
    </div>
  )
}
