import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { timerApi } from '../api/client'

export function useTimer() {
  const qc = useQueryClient()

  const { data: timer } = useQuery({
    queryKey: ['timer', 'current'],
    queryFn: timerApi.getCurrent,
    refetchInterval: 1000,
    // Only poll actively when the tab is in the foreground
    refetchIntervalInBackground: false,
  })

  const startTimer = useMutation({
    mutationFn: timerApi.start,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['timer'] }),
  })

  const pauseTimer = useMutation({
    mutationFn: timerApi.pause,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['timer'] }),
  })

  const stopTimer = useMutation({
    mutationFn: timerApi.stop,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['timer'] })
      qc.invalidateQueries({ queryKey: ['sessions'] })
    },
  })

  return { timer, startTimer, pauseTimer, stopTimer }
}
