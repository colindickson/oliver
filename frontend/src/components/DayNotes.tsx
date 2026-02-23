import { useRef, useState } from 'react'

interface DayNotesProps {
  label: string
  dayId: number
  initialContent: string
  onSave: (dayId: number, content: string) => Promise<unknown>
}

export function DayNotes({ label, dayId, initialContent, onSave }: DayNotesProps) {
  const [content, setContent] = useState(initialContent)
  const [saved, setSaved] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  function handleChange(value: string) {
    setContent(value)
    setSaved(false)

    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }

    debounceRef.current = setTimeout(async () => {
      await onSave(dayId, value)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    }, 1000)
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-stone-600 uppercase tracking-wide">
          {label}
        </h3>
        <span
          className={`text-xs text-moss-600 transition-opacity duration-300 ${
            saved ? 'opacity-100' : 'opacity-0'
          }`}
        >
          Saved
        </span>
      </div>
      <textarea
        value={content}
        onChange={e => handleChange(e.target.value)}
        placeholder={`Add ${label.toLowerCase()}…`}
        rows={3}
        className="w-full text-sm px-3 py-2.5 rounded-xl border border-stone-200 bg-white text-stone-800 placeholder-stone-300 resize-none focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent transition-shadow"
      />
    </div>
  )
}
