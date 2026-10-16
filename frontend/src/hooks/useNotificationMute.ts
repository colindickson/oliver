import { useState } from 'react'

const STORAGE_KEY = 'notifications_muted'

export function useNotificationMute() {
  const [muted, setMutedState] = useState<boolean>(
    () => localStorage.getItem(STORAGE_KEY) === 'true'
  )

  function toggleMuted() {
    setMutedState(prev => {
      const next = !prev
      localStorage.setItem(STORAGE_KEY, String(next))
      return next
    })
  }

  return { muted, toggleMuted }
}
