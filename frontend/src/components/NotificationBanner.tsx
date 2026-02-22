import { useReminders } from '../hooks/useReminders'

export function NotificationBanner() {
  const { dueReminders, markDelivered } = useReminders()

  if (dueReminders.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 flex flex-col gap-2 z-50 max-w-sm">
      {dueReminders.map(r => (
        <div
          key={r.id}
          className="bg-white border border-amber-300 shadow-lg rounded-lg p-4 flex items-start gap-3 transition-all duration-300"
        >
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-900">Reminder</p>
            <p className="text-sm text-gray-600 mt-0.5">{r.message}</p>
          </div>
          <button
            type="button"
            onClick={() => markDelivered.mutate(r.id)}
            className="text-gray-400 hover:text-gray-600 transition-colors text-xs flex-shrink-0 mt-0.5 leading-none"
            aria-label="Dismiss reminder"
          >
            &#x2715;
          </button>
        </div>
      ))}
    </div>
  )
}
