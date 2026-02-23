import { useState, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { tagApi } from '../api/client'

interface Props {
  value: string[]
  onChange: (tags: string[]) => void
  maxTags?: number
}

export function TagInput({ value, onChange, maxTags = 5 }: Props) {
  const [input, setInput] = useState('')
  const [open, setOpen] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const { data: allTags = [] } = useQuery({
    queryKey: ['tags', 'all'],
    queryFn: tagApi.getAll,
  })

  const suggestions = allTags
    .map(t => t.name)
    .filter(name => !value.includes(name) && name.startsWith(input.toLowerCase()))
    .slice(0, 6)

  function addTag(raw: string) {
    const tag = raw.trim().toLowerCase().replace(/^#/, '')
    if (!tag || value.includes(tag) || value.length >= maxTags) return
    onChange([...value, tag])
    setInput('')
    setOpen(false)
  }

  function removeTag(tag: string) {
    onChange(value.filter(t => t !== tag))
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' || e.key === ',' || e.key === ' ') {
      e.preventDefault()
      if (input.trim()) addTag(input)
    } else if (e.key === 'Backspace' && !input && value.length > 0) {
      removeTag(value[value.length - 1])
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  const atMax = value.length >= maxTags

  return (
    <div className="relative">
      <div
        className="flex flex-wrap gap-1 min-h-[36px] px-2 py-1.5 border border-stone-200 rounded-lg bg-white focus-within:ring-2 focus-within:ring-terracotta-300 focus-within:border-transparent transition-shadow cursor-text dark:bg-stone-800 dark:border-stone-600"
        onClick={() => inputRef.current?.focus()}
      >
        {value.map(tag => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-terracotta-50 text-terracotta-700 border border-terracotta-200 dark:bg-terracotta-900/30 dark:text-terracotta-300 dark:border-terracotta-700/30"
          >
            #{tag}
            <button
              type="button"
              onClick={e => { e.stopPropagation(); removeTag(tag) }}
              className="text-terracotta-400 hover:text-terracotta-600 leading-none dark:text-terracotta-500 dark:hover:text-terracotta-300"
              aria-label={`Remove #${tag}`}
            >
              ×
            </button>
          </span>
        ))}
        {!atMax && (
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => { setInput(e.target.value); setOpen(true) }}
            onKeyDown={handleKeyDown}
            onFocus={() => setOpen(true)}
            onBlur={() => setTimeout(() => setOpen(false), 150)}
            placeholder={value.length === 0 ? 'Add tags…' : ''}
            className="flex-1 min-w-[80px] text-xs outline-none bg-transparent placeholder-stone-400 dark:placeholder-stone-500"
          />
        )}
      </div>

      {/* Autocomplete dropdown */}
      {open && suggestions.length > 0 && (
        <ul className="absolute z-20 mt-1 w-full bg-white border border-stone-200 rounded-lg shadow-md overflow-hidden dark:bg-stone-700 dark:border-stone-600">
          {suggestions.map(name => (
            <li key={name}>
              <button
                type="button"
                onMouseDown={e => e.preventDefault()} // prevent blur-before-click
                onClick={() => addTag(name)}
                className="w-full text-left text-xs px-3 py-2 hover:bg-stone-50 text-stone-700 dark:text-stone-200 dark:hover:bg-stone-600"
              >
                #{name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
