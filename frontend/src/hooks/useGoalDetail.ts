import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { goalApi, type GoalCreate, type GoalUpdate } from '../api/client'

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

  const archiveGoal = useMutation({
    mutationFn: () => goalApi.archive(goalId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['goals', goalId] })
      qc.invalidateQueries({ queryKey: ['goals'] })
      qc.invalidateQueries({ queryKey: ['goals', 'archived'] })
      // Archiving a subtree can clear the focus setting server-side
      // (when the focus goal is in the archived subtree) — refresh it.
      qc.invalidateQueries({ queryKey: ['settings', 'focus-goal'] })
    },
  })

  const unarchiveGoal = useMutation({
    mutationFn: () => goalApi.unarchive(goalId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['goals', goalId] })
      qc.invalidateQueries({ queryKey: ['goals'] })
      qc.invalidateQueries({ queryKey: ['goals', 'archived'] })
    },
  })

  const createSubGoal = useMutation({
    mutationFn: (payload: GoalCreate) => goalApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['goals', goalId] })
      qc.invalidateQueries({ queryKey: ['goals'] })
    },
  })

  const detachSubGoal = useMutation({
    mutationFn: (childId: number) => goalApi.update(childId, { clear_parent: true }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['goals', goalId] })
      qc.invalidateQueries({ queryKey: ['goals'] })
    },
  })

  return { goal, isLoading, updateGoal, setStatus, archiveGoal, unarchiveGoal, createSubGoal, detachSubGoal }
}
