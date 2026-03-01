import { useEffect } from 'react'
import type { Notification } from '../api/client'

interface NotificationPopupProps {
  notification: Notification
  onDismiss: () => void
}

export function NotificationPopup({ notification, onDismiss }: NotificationPopupProps) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 10_000)
    return () => clearTimeout(timer)
  }, [notification.id, onDismiss])

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-sm animate-slide-up">
      <div className="bg-white border border-blue-200 shadow-soft-lg rounded-2xl p-4 flex items-start gap-3 dark:bg-stone-700 dark:border-blue-800/40">
        {/* Bell icon - blue tint */}
        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 dark:bg-blue-900/30">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="#2563eb" strokeWidth="1.5">
            <path d="M8 2a4.5 4.5 0 0 0-4.5 4.5c0 4 4.5 6 4.5 6s4.5-2 4.5-6A4.5 4.5 0 0 0 8 2z" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="8" cy="13.5" r="0.75" fill="#2563eb" stroke="none" />
          </svg>
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-blue-600 uppercase tracking-wider">{notification.source}</p>
          <p className="text-sm text-stone-700 dark:text-stone-200 mt-1">{notification.content}</p>
        </div>

        <button
          type="button"
          onClick={onDismiss}
          className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-stone-500 hover:bg-stone-100 rounded-lg transition-colors flex-shrink-0 dark:text-stone-500 dark:hover:text-stone-300 dark:hover:bg-stone-600"
          aria-label="Dismiss notification"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3.5 3.5L10.5 10.5M10.5 3.5L3.5 10.5" strokeLinecap="round" />
          </svg>
        </button>
      </div>
    </div>
  )
}
