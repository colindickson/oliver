import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { settingsApi, goalApi } from '../api/client'

export function useFocusGoal() {
  const qc = useQueryClient()

  const { data: focusSetting } = useQuery({
    queryKey: ['settings', 'focus-goal'],
    queryFn: settingsApi.getFocusGoal,
  })

  const { data: goal, isLoading: goalLoading } = useQuery({
    queryKey: ['goal', focusSetting?.goal_id],
    queryFn: () => focusSetting?.goal_id ? goalApi.getOne(focusSetting.goal_id) : null,
    enabled: focusSetting?.goal_id != null,
  })

  const setFocusGoal = useMutation({
    mutationFn: (goal_id: number | null) => settingsApi.setFocusGoal(goal_id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['settings', 'focus-goal'] })
      qc.invalidateQueries({ queryKey: ['goal'] })
    },
  })

  const clearFocusGoal = useMutation({
    mutationFn: () => settingsApi.setFocusGoal(null),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['settings', 'focus-goal'] })
    },
  })

  return {
    focusGoalId: focusSetting?.goal_id ?? null,
    focusGoal: goal ?? null,
    isLoading: goalLoading,
    setFocusGoal,
    clearFocusGoal,
  }
}
