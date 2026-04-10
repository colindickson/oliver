import { useEffect, useRef, useState } from 'react'

interface DayNotesProps {
  label: string
  dayId: number
  initialContent: string
  onSave: (dayId: number, content: string) => Promise<unknown>
}

export function DayNotes({ label, dayId, initialContent, onSave }: DayNotesProps) {
  const [content, setContent] = useState(initialContent)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const savedTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
      if (savedTimeoutRef.current) clearTimeout(savedTimeoutRef.current)
    }
  }, [])

  function handleChange(value: string) {
    setContent(value)
    setSaved(false)
    setError(false)

    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }

    debounceRef.current = setTimeout(async () => {
      try {
        await onSave(dayId, value)
        setSaved(true)
        savedTimeoutRef.current = setTimeout(() => setSaved(false), 2000)
      } catch {
        setError(true)
      }
    }, 1000)
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-stone-600 dark:text-stone-300 uppercase tracking-wide">
          {label}
        </h3>
        <span
          className={`text-xs transition-opacity duration-300 ${
            error
              ? 'opacity-100 text-red-600 dark:text-red-400'
              : saved
                ? 'opacity-100 text-moss-600 dark:text-moss-400'
                : 'opacity-0 text-moss-600 dark:text-moss-400'
          }`}
        >
          {error ? 'Save failed' : 'Saved'}
        </span>
      </div>
      <textarea
        value={content}
        onChange={e => handleChange(e.target.value)}
        placeholder={`Add ${label.toLowerCase()}…`}
        rows={3}
        className="w-full text-sm px-3 py-2.5 rounded-xl border border-stone-200 bg-white text-stone-800 placeholder-stone-300 resize-none focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent transition-shadow dark:bg-stone-700 dark:border-stone-600/50 dark:text-stone-100 dark:placeholder-stone-500"
      />
    </div>
  )
}
