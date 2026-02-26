import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { goalApi, type GoalUpdate } from '../api/client'

export function useGoalDetail(goalId: number | null) {
  const qc = useQueryClient()

  const { data: goal, isLoading } = useQuery({
    queryKey: ['goals', goalId],
    queryFn: () => goalApi.getOne(goalId!),
    enabled: goalId !== null,
  })

  const updateGoal = useMutation({
    mutationFn: (payload: GoalUpdate) => goalApi.update(goalId!, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['goals', goalId] })
      qc.invalidateQueries({ queryKey: ['goals'] })
    },
  })

  const setStatus = useMutation({
    mutationFn: (status: 'active' | 'completed') => goalApi.setStatus(goalId!, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['goals', goalId] })
      qc.invalidateQueries({ queryKey: ['goals'] })
    },
  })

  return { goal, isLoading, updateGoal, setStatus }
}
