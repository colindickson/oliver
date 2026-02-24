import { useState, useEffect, useRef, useCallback } from 'react'

interface Props {
  onConfirm: () => void
  onCancel?: () => void
  isLoading?: boolean
}

export function ConfirmableDelete({ onConfirm, onCancel, isLoading }: Props) {
  const [isConfirming, setIsConfirming] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const startConfirming = () => {
    setIsConfirming(true)
    // Auto-cancel after 5 seconds
    timeoutRef.current = setTimeout(() => {
      setIsConfirming(false)
    }, 5000)
  }

  const handleConfirm = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setIsConfirming(false)
    onConfirm()
  }

  const handleCancel = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setIsConfirming(false)
    onCancel?.()
  }, [onCancel])

  // Cancel on outside click
  useEffect(() => {
    if (!isConfirming) return

    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        handleCancel()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isConfirming, handleCancel])

  // Cancel on Escape key
  useEffect(() => {
    if (!isConfirming) return

    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        handleCancel()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isConfirming, handleCancel])

  if (!isConfirming) {
    return (
      <button
        type="button"
        onClick={startConfirming}
        disabled={isLoading}
        className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-red-400 hover:bg-red-50 rounded transition-colors dark:text-stone-600 dark:hover:text-red-400 dark:hover:bg-stone-700 disabled:opacity-50"
        aria-label="Delete task"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M3.5 4L4.5 12H9.5L10.5 4" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M2 4H12" strokeLinecap="round" />
          <path d="M5 4V2.5H9V4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
    )
  }

  return (
    <div
      ref={containerRef}
      className="flex items-center gap-1.5 transition-all duration-150"
    >
      <span className="text-xs text-stone-500 dark:text-stone-400">Delete?</span>
      <button
        type="button"
        onClick={handleConfirm}
        disabled={isLoading}
        className="text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 px-1.5 py-0.5 rounded transition-colors disabled:opacity-50"
        aria-label="Confirm delete"
      >
        Yes
      </button>
      <button
        type="button"
        onClick={handleCancel}
        className="text-xs text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-700 px-1.5 py-0.5 rounded transition-colors"
        aria-label="Cancel delete"
      >
        No
      </button>
    </div>
  )
}
