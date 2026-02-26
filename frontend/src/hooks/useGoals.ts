import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { goalApi, type GoalCreate } from '../api/client'

export function useGoals() {
  const qc = useQueryClient()

  const { data: goals = [], isLoading } = useQuery({
    queryKey: ['goals'],
    queryFn: goalApi.getAll,
  })

  const createGoal = useMutation({
    mutationFn: (payload: GoalCreate) => goalApi.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['goals'] }),
  })

  const deleteGoal = useMutation({
    mutationFn: (id: number) => goalApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['goals'] }),
  })

  return { goals, isLoading, createGoal, deleteGoal }
}
