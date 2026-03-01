import { useState, useRef, useEffect } from 'react'
import { useNotifications } from '../hooks/useNotifications'

function formatRelativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const btnRef = useRef<HTMLButtonElement>(null)
  const [dropdownPos, setDropdownPos] = useState<{ top: number; left: number } | null>(null)
  const { unreadNotifications, markRead, unreadCount } = useNotifications()

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    if (open) document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [open])

  function handleToggle() {
    if (!open && btnRef.current) {
      const rect = btnRef.current.getBoundingClientRect()
      setDropdownPos({ top: rect.bottom + 8, left: rect.left })
    }
    setOpen(o => !o)
  }

  return (
    <div ref={ref}>
      <button
        ref={btnRef}
        type="button"
        onClick={handleToggle}
        className="w-7 h-7 flex items-center justify-center rounded-lg text-stone-300 hover:text-stone-100 hover:bg-stone-700 transition-colors flex-shrink-0 relative"
        aria-label={unreadCount > 0 ? `Notifications, ${unreadCount} unread` : 'Notifications'}
      >
        {/* Bell SVG */}
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M7.5 1.5A3.5 3.5 0 0 0 4 5c0 3.5-1.5 4.5-1.5 4.5h9S10 8.5 10 5a3.5 3.5 0 0 0-2.5-3.5z" />
          <path d="M8.7 12.5a1.3 1.3 0 0 1-2.4 0" />
        </svg>
        {/* Red dot badge */}
        {unreadCount > 0 && (
          <span className="absolute top-0.5 right-0.5 w-2 h-2 bg-red-500 rounded-full" aria-hidden="true" />
        )}
      </button>

      {open && dropdownPos && (
        <div
          style={{ position: 'fixed', top: dropdownPos.top, left: dropdownPos.left }}
          className="w-80 bg-white dark:bg-stone-800 border border-stone-200 dark:border-stone-700 rounded-2xl shadow-soft-lg overflow-hidden z-50">
          <div className="px-4 py-3 border-b border-stone-100 dark:border-stone-700">
            <p className="text-sm font-semibold text-stone-700 dark:text-stone-200">Notifications</p>
          </div>

          {unreadNotifications.length === 0 ? (
            <div className="px-4 py-6 text-center text-sm text-stone-400">All caught up</div>
          ) : (
            <div className="divide-y divide-stone-100 dark:divide-stone-700">
              {unreadNotifications.map(n => (
                <div key={n.id} className="px-4 py-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-blue-600 uppercase tracking-wider">{n.source}</p>
                      <p className="text-sm text-stone-700 dark:text-stone-200 mt-0.5 break-words">{n.content}</p>
                      <p className="text-xs text-stone-400 mt-1">{formatRelativeTime(n.created_at)}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => markRead.mutate(n.id)}
                      className="text-xs text-stone-400 hover:text-stone-600 dark:hover:text-stone-300 whitespace-nowrap flex-shrink-0 mt-0.5"
                    >
                      Mark read
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
