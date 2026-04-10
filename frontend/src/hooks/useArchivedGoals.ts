import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { goalApi } from '../api/client'

export function useArchivedGoals() {
  const qc = useQueryClient()

  const { data: goals = [], isLoading, isError } = useQuery({
    queryKey: ['goals', 'archived'],
    queryFn: goalApi.getArchived,
  })

  const unarchiveGoal = useMutation({
    mutationFn: (id: number) => goalApi.unarchive(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['goals', 'archived'] })
      qc.invalidateQueries({ queryKey: ['goals'] })
    },
  })

  const deleteGoal = useMutation({
    mutationFn: (id: number) => goalApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['goals', 'archived'] })
    },
  })

  return { goals, isLoading, isError, unarchiveGoal, deleteGoal }
}
