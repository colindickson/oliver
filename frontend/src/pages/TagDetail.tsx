import { Link, useParams } from 'react-router-dom'
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { tagApi } from '../api/client'
import { Sidebar } from '../components/Sidebar'
import { useMobile } from '../contexts/MobileContext'
import { MobileHeader } from '../components/MobileHeader'
import { BottomTabBar } from '../components/BottomTabBar'
import { useTagFilters } from '../hooks/useTagFilters'
import { PeriodSelector } from '../components/PeriodSelector'
import { IncompleteToggle } from '../components/IncompleteToggle'

// Filter groups to a date window (excluding today, matching Tags behavior)
function filterDaysToWindow<T extends { date: string }>(items: T[], windowDays: number): T[] {
  const cutoff = new Date()
  cutoff.setDate(cutoff.getDate() - windowDays)
  const cutoffStr = cutoff.toISOString().slice(0, 10)
  const todayStr = new Date().toISOString().slice(0, 10)
  return items.filter(item =>
    item.date === 'backlog' || (item.date >= cutoffStr && item.date < todayStr)
  )
}

export function TagDetail() {
  const { tagName } = useParams<{ tagName: string }>()
  const decoded = tagName ? decodeURIComponent(tagName) : ''
  const isMobile = useMobile()
  const { periodDays, showIncompleteOnly, setPeriodDays, setShowIncompleteOnly, filterParams } = useTagFilters()

  const { data: rawGroups = [], isLoading, isError } = useQuery({
    queryKey: ['tags', decoded, 'tasks'],
    queryFn: () => tagApi.getTasksForTag(decoded),
    enabled: !!decoded,
  })

  // Apply filters to groups
  const filteredGroups = useMemo(() => {
    // Filter groups by date range
    let groups = rawGroups
    if (periodDays !== 'all') {
      groups = filterDaysToWindow(groups, periodDays)
    }

    // Always exclude rolled_forward tasks (superseded by their successor)
    groups = groups.map(g => ({
      ...g,
      tasks: g.tasks.filter(t => t.status !== 'rolled_forward')
    })).filter(g => g.tasks.length > 0)

    // Filter tasks within groups by incomplete status
    if (showIncompleteOnly) {
      groups = groups.map(g => ({
        ...g,
        tasks: g.tasks.filter(t => t.status === 'pending' || t.status === 'in_progress')
      })).filter(g => g.tasks.length > 0)
    }

    return groups
  }, [rawGroups, periodDays, showIncompleteOnly])

  const totalTasks = filteredGroups.reduce((sum, g) => sum + g.tasks.length, 0)

  if (isMobile) {
    return (
      <div className="flex flex-col h-screen bg-stone-900">
        <MobileHeader title={decoded ? `#${decoded}` : 'Tag'} />
        <div className="flex-1 overflow-y-auto pb-14">
          {/* Filter controls */}
          <div className="px-4 py-3 border-b border-stone-700 space-y-3">
            <PeriodSelector value={periodDays} onChange={setPeriodDays} />
            <IncompleteToggle checked={showIncompleteOnly} onChange={setShowIncompleteOnly} />
          </div>

          <div className="px-4 py-4">
            {isLoading && (
              <div className="flex items-center justify-center h-48 text-stone-400 text-sm">
                Loading...
              </div>
            )}

            {isError && (
              <div className="bg-terracotta-50 border border-terracotta-200 rounded-2xl p-6 text-center">
                <p className="text-terracotta-600">Tag not found.</p>
              </div>
            )}

            {!isLoading && !isError && filteredGroups.length === 0 && (
              <div className="flex flex-col items-center justify-center h-48 text-center">
                <p className="text-stone-400 text-sm">
                  {showIncompleteOnly ? 'No incomplete tasks with this tag.' : 'No tasks with this tag.'}
                </p>
                <p className="text-stone-300 text-xs mt-1">
                  {showIncompleteOnly ? 'Try adjusting your filters.' : periodDays !== 'all' ? 'Try expanding the time range.' : ''}
                </p>
              </div>
            )}

            {filteredGroups.length > 0 && (
              <div className="space-y-6 animate-fade-in">
                {filteredGroups.map(group => (
                  <div key={group.date}>
                    {group.date === 'backlog' ? (
                      <span className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-2 inline-block dark:text-stone-500">
                        Backlog
                      </span>
                    ) : (
                      <Link
                        to={`/day/${group.date}`}
                        className="text-xs font-semibold uppercase tracking-wide text-stone-400 hover:text-terracotta-500 transition-colors mb-2 inline-block dark:text-stone-500 dark:hover:text-terracotta-400"
                      >
                        {new Date(group.date + 'T12:00:00').toLocaleDateString('en-US', {
                          weekday: 'long',
                          month: 'long',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </Link>
                    )}
                    <div className="space-y-2">
                      {group.tasks.map(task => (
                        <div
                          key={task.id}
                          className="bg-white rounded-xl border border-stone-100 p-3 shadow-sm flex items-start gap-3 dark:bg-stone-800 dark:border-stone-700/50"
                        >
                          <div
                            className={`mt-0.5 w-4 h-4 rounded-full flex-shrink-0 ${
                              task.status === 'completed' ? 'bg-moss-500' : 'bg-stone-200 dark:bg-stone-600'
                            }`}
                          />
                          <div className="flex-1 min-w-0">
                            <p
                              className={`text-sm font-medium ${
                                task.status === 'completed'
                                  ? 'line-through text-stone-400'
                                  : 'text-stone-800 dark:text-stone-100'
                              }`}
                            >
                              {task.title}
                            </p>
                            {task.tags && task.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-1">
                                {task.tags.map(tag => (
                                  <Link
                                    key={tag}
                                    to={`/tags/${encodeURIComponent(tag)}`}
                                    className={`text-xs px-1.5 py-0.5 rounded-full transition-colors ${
                                      tag === decoded
                                        ? 'bg-terracotta-100 text-terracotta-600 dark:bg-terracotta-900/30 dark:text-terracotta-300'
                                        : 'bg-stone-100 text-stone-500 hover:bg-terracotta-50 hover:text-terracotta-600 dark:bg-stone-700 dark:text-stone-400'
                                    }`}
                                  >
                                    #{tag}
                                  </Link>
                                ))}
                              </div>
                            )}
                          </div>
                          {task.category && (
                            <span className="text-xs text-stone-400 flex-shrink-0 capitalize">
                              {task.category.replace('_', ' ')}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
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

      <div className="flex-1 flex flex-col min-w-0">
        <header className="bg-white/80 backdrop-blur-sm border-b border-stone-200 px-8 py-5 flex-shrink-0 dark:bg-stone-850 dark:border-stone-700/50">
          <div className="flex items-center justify-between">
            <div>
              <Link
                to={`/tags${filterParams}`}
                className="text-sm text-stone-400 hover:text-stone-600 mb-2 flex items-center gap-1 transition-colors"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M10 4L6 8L10 12" />
                </svg>
                All Tags
              </Link>
              <h1 className="text-xl font-semibold text-stone-800 dark:text-stone-100">#{decoded}</h1>
              <p className="text-sm text-stone-400 mt-0.5">
                {totalTasks} {totalTasks === 1 ? 'task' : 'tasks'}
                {periodDays !== 'all' ? ` · Last ${periodDays} days` : ' · All time'}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <PeriodSelector value={periodDays} onChange={setPeriodDays} />
              <IncompleteToggle checked={showIncompleteOnly} onChange={setShowIncompleteOnly} />
            </div>
          </div>
        </header>

        <main className="flex-1 p-8 max-w-2xl overflow-auto">
          {isLoading && (
            <div className="flex items-center justify-center h-48 text-stone-400 text-sm">
              Loading...
            </div>
          )}

          {isError && (
            <div className="bg-terracotta-50 border border-terracotta-200 rounded-2xl p-6 text-center">
              <p className="text-terracotta-600">Tag not found.</p>
            </div>
          )}

          {!isLoading && !isError && filteredGroups.length === 0 && (
            <div className="flex flex-col items-center justify-center h-48 text-center">
              <p className="text-stone-400 text-sm">
                {showIncompleteOnly ? 'No incomplete tasks with this tag.' : 'No tasks with this tag.'}
              </p>
              <p className="text-stone-300 text-xs mt-1">
                {showIncompleteOnly ? 'Try adjusting your filters.' : periodDays !== 'all' ? 'Try expanding the time range.' : ''}
              </p>
            </div>
          )}

          {filteredGroups.length > 0 && (
            <div className="space-y-6 animate-fade-in">
              {filteredGroups.map(group => (
                <div key={group.date}>
                  {group.date === 'backlog' ? (
                    <span className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-2 inline-block dark:text-stone-500">
                      Backlog
                    </span>
                  ) : (
                    <Link
                      to={`/day/${group.date}`}
                      className="text-xs font-semibold uppercase tracking-wide text-stone-400 hover:text-terracotta-500 transition-colors mb-2 inline-block dark:text-stone-500 dark:hover:text-terracotta-400"
                    >
                      {new Date(group.date + 'T12:00:00').toLocaleDateString('en-US', {
                        weekday: 'long',
                        month: 'long',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </Link>
                  )}
                  <div className="space-y-2">
                    {group.tasks.map(task => (
                      <div
                        key={task.id}
                        className="bg-white rounded-xl border border-stone-100 p-3 shadow-sm flex items-start gap-3 dark:bg-stone-800 dark:border-stone-700/50"
                      >
                        <div
                          className={`mt-0.5 w-4 h-4 rounded-full flex-shrink-0 ${
                            task.status === 'completed' ? 'bg-moss-500' : 'bg-stone-200 dark:bg-stone-600'
                          }`}
                        />
                        <div className="flex-1 min-w-0">
                          <p
                            className={`text-sm font-medium ${
                              task.status === 'completed'
                                ? 'line-through text-stone-400'
                                : 'text-stone-800 dark:text-stone-100'
                            }`}
                          >
                            {task.title}
                          </p>
                          {task.tags && task.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {task.tags.map(tag => (
                                <Link
                                  key={tag}
                                  to={`/tags/${encodeURIComponent(tag)}`}
                                  className={`text-xs px-1.5 py-0.5 rounded-full transition-colors ${
                                    tag === decoded
                                      ? 'bg-terracotta-100 text-terracotta-600 dark:bg-terracotta-900/30 dark:text-terracotta-300'
                                      : 'bg-stone-100 text-stone-500 hover:bg-terracotta-50 hover:text-terracotta-600 dark:bg-stone-700 dark:text-stone-400'
                                  }`}
                                >
                                  #{tag}
                                </Link>
                              ))}
                            </div>
                          )}
                        </div>
                        {task.category && (
                          <span className="text-xs text-stone-400 flex-shrink-0 capitalize">
                            {task.category.replace('_', ' ')}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
