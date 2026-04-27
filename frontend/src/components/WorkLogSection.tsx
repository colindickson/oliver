import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workLogApi } from '../api/client'
import type { WorkLog } from '../api/client'
import { TagInput } from './TagInput'

interface Props {
  date: string
}

interface EntryTagEditorProps {
  entry: WorkLog
  date: string
}

function EntryTagEditor({ entry, date }: EntryTagEditorProps) {
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [draftTags, setDraftTags] = useState<string[]>(entry.tags)

  const updateTags = useMutation({
    mutationFn: (tags: string[]) => workLogApi.updateTags(entry.id, tags),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['work-logs', date] })
      setEditing(false)
    },
    onError: () => {
      console.error('Failed to update work log tags')
    },
  })

  if (editing) {
    return (
      <div className="mt-2 space-y-2">
        <TagInput
          value={draftTags}
          onChange={setDraftTags}
        />
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => updateTags.mutate(draftTags)}
            disabled={updateTags.isPending}
            className="text-xs bg-stone-800 text-white rounded-lg px-3 py-1.5 hover:bg-stone-700 disabled:opacity-50 transition-all dark:bg-stone-600 dark:hover:bg-stone-500"
          >
            Save
          </button>
          <button
            type="button"
            onClick={() => {
              setDraftTags(entry.tags)
              setEditing(false)
            }}
            className="text-xs text-stone-400 hover:text-stone-600 transition-colors px-2 dark:text-stone-500 dark:hover:text-stone-300"
          >
            Cancel
          </button>
        </div>
      </div>
    )
  }

  if (entry.tags.length > 0) {
    return (
      <button
        type="button"
        className="flex flex-wrap gap-1 mt-2 text-left"
        onClick={() => setEditing(true)}
        title="Click to edit tags"
      >
        {entry.tags.map(tag => (
          <span
            key={tag}
            className="text-xs px-1.5 py-0.5 rounded-full bg-stone-100 text-stone-500 dark:bg-stone-700 dark:text-stone-400"
          >
            #{tag}
          </span>
        ))}
      </button>
    )
  }

  return (
    <button
      type="button"
      onClick={() => setEditing(true)}
      className="mt-1.5 text-xs text-stone-400 hover:text-stone-600 dark:text-stone-500 dark:hover:text-stone-300 transition-colors"
    >
      + add tags
    </button>
  )
}

export function WorkLogSection({ date }: Props) {
  const [expanded, setExpanded] = useState(false)

  const { data: entries = [], isLoading } = useQuery({
    queryKey: ['work-logs', date],
    queryFn: () => workLogApi.listByDate(date),
    enabled: expanded,
  })

  return (
    <div className="rounded-2xl border border-stone-200 dark:border-stone-700/50 bg-white dark:bg-stone-800/50">
      {/* Header */}
      <button
        type="button"
        className="w-full flex items-center justify-between px-5 py-4"
        onClick={() => setExpanded(prev => !prev)}
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-stone-500 dark:text-stone-400 uppercase tracking-wide">
            Work Log
          </span>
          {expanded && entries.length > 0 && (
            <span className="text-xs font-medium px-1.5 py-0.5 rounded-full bg-stone-100 dark:bg-stone-700 text-stone-500 dark:text-stone-400">
              {entries.length}
            </span>
          )}
        </div>
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className={`text-stone-400 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
        >
          <path d="M4 6l4 4 4-4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {/* Body */}
      {expanded && (
        <div className="px-5 pb-5 space-y-4">
          {isLoading ? (
            <p className="text-sm text-stone-400 dark:text-stone-500">Loading…</p>
          ) : entries.length === 0 ? (
            <p className="text-sm italic text-stone-400 dark:text-stone-500">
              No work logged for this day yet.
            </p>
          ) : (
            entries.map(entry => {
              const time = new Date(entry.created_at).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })
              return (
                <div
                  key={entry.id}
                  className="border-b border-stone-100 dark:border-stone-700/50 last:border-0 pb-4 last:pb-0"
                >
                  <div className="flex items-baseline gap-2">
                    <span className="text-sm font-semibold text-stone-800 dark:text-stone-100">
                      {entry.project_name}
                    </span>
                    <span className="text-xs text-stone-400 dark:text-stone-500 tabular-nums">
                      {time}
                    </span>
                  </div>
                  {entry.description && (
                    <p className="text-sm text-stone-600 dark:text-stone-300 mt-0.5 whitespace-pre-wrap">
                      {entry.description}
                    </p>
                  )}
                  <EntryTagEditor entry={entry} date={date} />
                </div>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}
