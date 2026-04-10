import { useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { Task } from '../api/client'
import { taskApi } from '../api/client'

interface UseTaskEditOptions {
  task: Task
  onSuccess?: () => void
}

interface UseTaskEditReturn {
  editing: boolean
  editTitle: string
  editDescription: string
  editTags: string[]
  saving: boolean
  saveError: string | null
  openEdit: () => void
  saveEdit: () => Promise<void>
  cancelEdit: () => void
  setEditTitle: (title: string) => void
  setEditDescription: (description: string) => void
  setEditTags: (tags: string[]) => void
}

export function useTaskEdit({ task, onSuccess }: UseTaskEditOptions): UseTaskEditReturn {
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(task.title)
  const [editDescription, setEditDescription] = useState(task.description ?? '')
  const [editTags, setEditTags] = useState<string[]>(task.tags ?? [])
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const openEdit = useCallback(() => {
    setEditTitle(task.title)
    setEditDescription(task.description ?? '')
    setEditTags(task.tags ?? [])
    setSaveError(null)
    setEditing(true)
  }, [task.id, task.title, task.description, task.tags])

  const saveEdit = useCallback(async () => {
    if (!editTitle.trim()) return
    setSaving(true)
    setSaveError(null)
    try {
      await taskApi.update(task.id, {
        title: editTitle.trim(),
        description: editDescription.trim() || null,
        tags: editTags,
      })
      qc.invalidateQueries({ queryKey: ['day'] })
      qc.invalidateQueries({ queryKey: ['tags'] })
      setEditing(false)
      onSuccess?.()
    } catch {
      setSaveError('Failed to save. Please try again.')
    } finally {
      setSaving(false)
    }
  }, [task.id, editTitle, editDescription, editTags, qc, onSuccess])

  const cancelEdit = useCallback(() => {
    setSaveError(null)
    setEditing(false)
  }, [])

  return {
    editing,
    editTitle,
    editDescription,
    editTags,
    saving,
    saveError,
    openEdit,
    saveEdit,
    cancelEdit,
    setEditTitle,
    setEditDescription,
    setEditTags,
  }
}
