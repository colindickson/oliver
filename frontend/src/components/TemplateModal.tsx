import { useState, useEffect, useCallback } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { templatesApi, type TaskTemplate } from '../api/client'
import { TagInput } from './TagInput'

type Category = 'deep_work' | 'short_task' | 'maintenance'

const CATEGORY_LABELS: Record<Category, string> = {
  deep_work: 'Deep Work',
  short_task: 'Short Task',
  maintenance: 'Maintenance',
}

interface Props {
  template: TaskTemplate | null  // null = create mode
  onClose: () => void
}

export function TemplateModal({ template, onClose }: Props) {
  const qc = useQueryClient()
  const isEditing = template !== null

  const [title, setTitle] = useState(template?.title ?? '')
  const [description, setDescription] = useState(template?.description ?? '')
  const [category, setCategory] = useState<Category | ''>(template?.category as Category ?? '')
  const [tags, setTags] = useState<string[]>(template?.tags ?? [])
  const [error, setError] = useState('')

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose()
  }, [onClose])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  const save = useMutation({
    mutationFn: async () => {
      const payload = {
        title: title.trim(),
        description: description.trim() || null,
        category: category || null,
        tags,
      }
      if (isEditing) {
        return templatesApi.update(template.id, payload)
      }
      return templatesApi.create(payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['templates'] })
      onClose()
    },
    onError: () => {
      setError('Failed to save template. Please try again.')
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim()) {
      setError('Title is required.')
      return
    }
    setError('')
    save.mutate()
  }

  return (
    <div
      className="fixed inset-0 bg-stone-900/50 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="template-modal-title"
        className="bg-white rounded-2xl shadow-soft-lg p-6 w-full max-w-sm mx-4 animate-slide-up dark:bg-stone-700"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-terracotta-100 dark:bg-terracotta-900/30 flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-terracotta-600 dark:text-terracotta-400" aria-hidden="true">
              <rect x="3" y="3" width="14" height="14" rx="2" />
              <path d="M7 8h6M7 12h4" strokeLinecap="round" />
            </svg>
          </div>
          <h2 id="template-modal-title" className="text-base font-semibold text-stone-800 dark:text-stone-100">
            {isEditing ? 'Edit Template' : 'New Template'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div>
            <label className="text-xs font-medium text-stone-500 uppercase tracking-wider block mb-1.5">
              Title <span className="text-terracotta-500">*</span>
            </label>
            <input
              autoFocus
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="Template title"
              className="w-full text-sm border border-stone-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent transition-shadow dark:bg-stone-800 dark:border-stone-600 dark:text-stone-100"
            />
          </div>

          {/* Description */}
          <div>
            <label className="text-xs font-medium text-stone-500 uppercase tracking-wider block mb-1.5">
              Description
            </label>
            <input
              type="text"
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Optional description"
              className="w-full text-sm border border-stone-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent transition-shadow dark:bg-stone-800 dark:border-stone-600 dark:text-stone-100"
            />
          </div>

          {/* Category */}
          <div>
            <label className="text-xs font-medium text-stone-500 uppercase tracking-wider block mb-1.5">
              Category
            </label>
            <select
              value={category}
              onChange={e => setCategory(e.target.value as Category | '')}
              className="w-full text-sm border border-stone-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-terracotta-300 focus:border-transparent transition-shadow dark:bg-stone-800 dark:border-stone-600 dark:text-stone-100"
            >
              <option value="">No category</option>
              {(Object.keys(CATEGORY_LABELS) as Category[]).map(cat => (
                <option key={cat} value={cat}>{CATEGORY_LABELS[cat]}</option>
              ))}
            </select>
          </div>

          {/* Tags */}
          <div>
            <label className="text-xs font-medium text-stone-500 uppercase tracking-wider block mb-1.5">
              Tags
            </label>
            <TagInput value={tags} onChange={setTags} />
          </div>

          {error && (
            <p className="text-xs text-terracotta-600 dark:text-terracotta-400">{error}</p>
          )}

          {/* Actions */}
          <div className="flex gap-2 pt-1">
            <button
              type="submit"
              disabled={save.isPending}
              className="flex-1 text-sm bg-stone-800 text-white rounded-lg px-4 py-2 hover:bg-stone-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all dark:bg-stone-600 dark:hover:bg-stone-500"
            >
              {save.isPending ? 'Saving…' : isEditing ? 'Save changes' : 'Create'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="text-sm text-stone-400 hover:text-stone-600 transition-colors px-3 dark:text-stone-500 dark:hover:text-stone-300"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
