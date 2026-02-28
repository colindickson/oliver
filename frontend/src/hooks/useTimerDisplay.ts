import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '../api/client'

export function useTimerDisplay() {
  const qc = useQueryClient()
  const { data } = useQuery({
    queryKey: ['settings', 'timer-display'],
    queryFn: settingsApi.getTimerDisplay,
  })
  const showTimer = data?.enabled ?? true

  const toggle = useMutation({
    mutationFn: (enabled: boolean) => settingsApi.setTimerDisplay(enabled),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['settings', 'timer-display'] }),
  })

  return { showTimer, toggle }
}
