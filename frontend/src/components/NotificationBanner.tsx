import { useReminders } from '../hooks/useReminders'

export function NotificationBanner() {
  const { dueReminders, markDelivered } = useReminders()

  if (dueReminders.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 flex flex-col gap-3 z-50 max-w-sm">
      {dueReminders.map(r => (
        <div
          key={r.id}
          className="bg-white border border-amber-200 shadow-soft-lg rounded-2xl p-4 flex items-start gap-3 animate-slide-up dark:bg-stone-700 dark:border-amber-800/40"
        >
          {/* Bell icon */}
          <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0 dark:bg-amber-900/30">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="#d97706" strokeWidth="1.5">
              <path d="M8 14C8 14 12 11 12 7C12 4.5 10.2 2.5 8 2.5C5.8 2.5 4 4.5 4 7C4 11 8 14 8 14Z" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M8 5V7" strokeLinecap="round" />
            </svg>
          </div>

          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-amber-600 uppercase tracking-wider">Reminder</p>
            <p className="text-sm text-stone-700 dark:text-stone-200 mt-1">{r.message}</p>
          </div>

          <button
            type="button"
            onClick={() => markDelivered.mutate(r.id)}
            className="w-6 h-6 flex items-center justify-center text-stone-300 hover:text-stone-500 hover:bg-stone-100 rounded-lg transition-colors flex-shrink-0 dark:text-stone-500 dark:hover:text-stone-300 dark:hover:bg-stone-600"
            aria-label="Dismiss reminder"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3.5 3.5L10.5 10.5M10.5 3.5L3.5 10.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  )
}
