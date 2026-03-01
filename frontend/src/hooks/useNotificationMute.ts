import { useState, useEffect } from 'react'
import { useTimer } from './useTimer'

const STORAGE_KEY = 'notifications_muted'

export function useNotificationMute() {
  const [muted, setMutedState] = useState<boolean>(
    () => localStorage.getItem(STORAGE_KEY) === 'true'
  )

  const { timer } = useTimer()

  function setMuted(value: boolean) {
    setMutedState(value)
    localStorage.setItem(STORAGE_KEY, String(value))
  }

  function toggleMuted() {
    setMuted(!muted)
  }

  // Auto-mute when timer starts running; auto-unmute when paused or stopped
  useEffect(() => {
    if (timer?.status === 'running') {
      setMuted(true)
    } else if (timer?.status === 'paused' || timer?.status === 'idle') {
      setMuted(false)
    }
  }, [timer?.status])

  return { muted, toggleMuted }
}
