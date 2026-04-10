import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { dayApi, backlogApi } from '../api/client'
import type { Task, DayResponse } from '../api/client'
import { Sidebar } from '../components/Sidebar'
import { useMobile } from '../contexts/MobileContext'
import { MobileHeader } from '../components/MobileHeader'
import { BottomTabBar } from '../components/BottomTabBar'
import { useTagFilters } from '../hooks/useTagFilters'
import { PeriodSelector } from '../components/PeriodSelector'
import { IncompleteToggle } from '../components/IncompleteToggle'

// Filter days to a date window (excluding today, matching Analytics behavior)
function filterDaysToWindow(days: DayResponse[], windowDays: number): DayResponse[] {
  const cutoff = new Date()
  cutoff.setDate(cutoff.getDate() - windowDays)
  const cutoffStr = cutoff.toISOString().slice(0, 10)
  const todayStr = new Date().toISOString().slice(0, 10)
  return days.filter(d => d.date >= cutoffStr && d.date < todayStr)
}

export function Tags() {
  const { periodDays, showIncompleteOnly, setPeriodDays, setShowIncompleteOnly, filterParams } = useTagFilters()

  const { data: days = [], isLoading: daysLoading, isError } = useQuery({
    queryKey: ['days', 'all'],
    queryFn: dayApi.getAll,
  })

  const { data: backlogTasks = [], isLoading: backlogLoading } = useQuery({
    queryKey: ['backlog'],
    queryFn: () => backlogApi.list(),
  })

  // Aggregate tags from day tasks and backlog tasks
  const filteredTags = useMemo(() => {
    // 1. Filter days by date window if not 'all'
    let filteredDays = days
    if (periodDays !== 'all') {
      filteredDays = filterDaysToWindow(days, periodDays)
    }

    // 2. Collect tasks from filtered days + backlog
    const dayTasks = filteredDays.flatMap(d => d.tasks)
    const allTasks: Task[] = [...dayTasks, ...backlogTasks]

    // 3. Aggregate tags with counts
    const tagMap = new Map<string, { total: number; incomplete: number }>()
    for (const task of allTasks) {
      for (const tagName of task.tags) {
        const existing = tagMap.get(tagName) ?? { total: 0, incomplete: 0 }
        existing.total += 1
        if (task.status === 'pending' || task.status === 'in_progress') {
          existing.incomplete += 1
        }
        tagMap.set(tagName, existing)
      }
    }

    // 4. Convert to array and filter by incomplete if needed
    let result = Array.from(tagMap.entries()).map(([name, counts]) => ({
      name,
      task_count: counts.total,
      incomplete_count: counts.incomplete,
    }))

    if (showIncompleteOnly) {
      result = result.filter(t => t.incomplete_count > 0)
    }

    // 5. Sort by count descending, then alphabetically
    result.sort((a, b) => b.task_count - a.task_count || a.name.localeCompare(b.name))

    return result
  }, [days, backlogTasks, periodDays, showIncompleteOnly])

  const isLoading = daysLoading || backlogLoading
  const isMobile = useMobile()

  if (isError) {
    if (isMobile) {
      return (
        <div className="flex flex-col h-screen bg-stone-900">
          <MobileHeader title="Tags" />
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <p className="text-stone-400 text-sm">Failed to load tags.</p>
          </div>
          <BottomTabBar />
        </div>
      )
    }
    return (
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <p className="text-stone-400 text-sm">Failed to load tags.</p>
        </div>
      </div>
    )
  }

  if (isMobile) {
    return (
      <div className="flex flex-col h-screen bg-stone-900">
        <MobileHeader title="Tags" />
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

            {!isLoading && filteredTags.length === 0 && (
              <div className="flex flex-col items-center justify-center h-48 text-center">
                <p className="text-stone-400 text-sm">
                  {showIncompleteOnly ? 'No tags with incomplete tasks.' : 'No tags yet.'}
                </p>
                <p className="text-stone-300 text-xs mt-1">
                  {showIncompleteOnly ? 'Try adjusting your filters.' : 'Add tags when creating or editing tasks.'}
                </p>
              </div>
            )}

            {filteredTags.length > 0 && (
              <div className="flex flex-wrap gap-3">
                {filteredTags.map(tag => (
                  <Link
                    key={tag.name}
                    to={`/tags/${encodeURIComponent(tag.name)}${filterParams}`}
                    className="group flex items-center gap-2 px-4 py-2.5 bg-white rounded-xl border border-stone-200 shadow-sm hover:border-terracotta-300 hover:shadow-md transition-all dark:bg-stone-700 dark:border-stone-600 dark:hover:border-terracotta-600/50"
                  >
                    <span className="text-sm font-medium text-stone-700 group-hover:text-terracotta-600 transition-colors dark:text-stone-200 dark:group-hover:text-terracotta-300">
                      #{tag.name}
                    </span>
                    <span className="text-xs text-stone-400 tabular-nums bg-stone-100 px-1.5 py-0.5 rounded-full dark:text-stone-400 dark:bg-stone-600">
                      {tag.task_count}
                    </span>
                  </Link>
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
              <h1 className="text-xl font-semibold text-stone-800 dark:text-stone-100">Tags</h1>
              <p className="text-sm text-stone-400 mt-0.5">
                {periodDays === 'all' ? 'All time' : `Last ${periodDays} days`}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <PeriodSelector value={periodDays} onChange={setPeriodDays} />
              <IncompleteToggle checked={showIncompleteOnly} onChange={setShowIncompleteOnly} />
            </div>
          </div>
        </header>

        <main className="flex-1 p-8 overflow-auto">
          {isLoading && (
            <div className="flex items-center justify-center h-48 text-stone-400 text-sm">
              Loading...
            </div>
          )}

          {!isLoading && filteredTags.length === 0 && (
            <div className="flex flex-col items-center justify-center h-48 text-center">
              <p className="text-stone-400 text-sm">
                {showIncompleteOnly ? 'No tags with incomplete tasks.' : 'No tags yet.'}
              </p>
              <p className="text-stone-300 text-xs mt-1">
                {showIncompleteOnly ? 'Try adjusting your filters.' : 'Add tags when creating or editing tasks.'}
              </p>
            </div>
          )}

          {filteredTags.length > 0 && (
            <div className="flex flex-wrap gap-3 max-w-2xl">
              {filteredTags.map(tag => (
                <Link
                  key={tag.name}
                  to={`/tags/${encodeURIComponent(tag.name)}${filterParams}`}
                  className="group flex items-center gap-2 px-4 py-2.5 bg-white rounded-xl border border-stone-200 shadow-sm hover:border-terracotta-300 hover:shadow-md transition-all dark:bg-stone-700 dark:border-stone-600 dark:hover:border-terracotta-600/50"
                >
                  <span className="text-sm font-medium text-stone-700 group-hover:text-terracotta-600 transition-colors dark:text-stone-200 dark:group-hover:text-terracotta-300">
                    #{tag.name}
                  </span>
                  <span className="text-xs text-stone-400 tabular-nums bg-stone-100 px-1.5 py-0.5 rounded-full dark:text-stone-400 dark:bg-stone-600">
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
