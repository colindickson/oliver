import { useState, useEffect, useRef } from 'react'
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
    setMutedState(prev => {
      const next = !prev
      localStorage.setItem(STORAGE_KEY, String(next))
      return next
    })
  }

  const isMounted = useRef(false)

  // Auto-mute on timer start; auto-unmute on pause/stop (skip initial mount)
  useEffect(() => {
    if (!isMounted.current) {
      isMounted.current = true
      return
    }
    if (timer?.status === 'running') {
      setMutedState(true)
      localStorage.setItem(STORAGE_KEY, 'true')
    } else if (timer?.status === 'paused' || timer?.status === 'idle') {
      setMutedState(false)
      localStorage.setItem(STORAGE_KEY, 'false')
    }
    // setMutedState is stable (from useState), STORAGE_KEY is a module constant
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timer?.status])

  return { muted, toggleMuted }
}
