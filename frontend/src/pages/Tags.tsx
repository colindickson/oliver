import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { tagApi } from '../api/client'
import { Sidebar } from '../components/Sidebar'

export function Tags() {
  const { data: tags = [], isLoading } = useQuery({
    queryKey: ['tags', 'all'],
    queryFn: tagApi.getAll,
  })

  return (
    <div className="flex min-h-screen bg-stone-25">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        <header className="bg-white/80 backdrop-blur-sm border-b border-stone-200 px-8 py-5 flex-shrink-0">
          <h1 className="text-xl font-semibold text-stone-800">Tags</h1>
          <p className="text-sm text-stone-400 mt-0.5">All tags used across your tasks</p>
        </header>

        <main className="flex-1 p-8">
          {isLoading && (
            <div className="flex items-center justify-center h-48 text-stone-400 text-sm">
              Loading...
            </div>
          )}

          {!isLoading && tags.length === 0 && (
            <div className="flex flex-col items-center justify-center h-48 text-center">
              <p className="text-stone-400 text-sm">No tags yet.</p>
              <p className="text-stone-300 text-xs mt-1">Add tags when creating or editing tasks.</p>
            </div>
          )}

          {tags.length > 0 && (
            <div className="flex flex-wrap gap-3 max-w-2xl">
              {tags.map(tag => (
                <Link
                  key={tag.id}
                  to={`/tags/${encodeURIComponent(tag.name)}`}
                  className="group flex items-center gap-2 px-4 py-2.5 bg-white rounded-xl border border-stone-200 shadow-sm hover:border-terracotta-300 hover:shadow-md transition-all"
                >
                  <span className="text-sm font-medium text-stone-700 group-hover:text-terracotta-600 transition-colors">
                    #{tag.name}
                  </span>
                  <span className="text-xs text-stone-400 tabular-nums bg-stone-100 px-1.5 py-0.5 rounded-full">
                    {tag.task_count}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
