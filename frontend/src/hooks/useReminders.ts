import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reminderApi } from '../api/client'

export function useReminders() {
  const qc = useQueryClient()

  const { data: dueReminders = [] } = useQuery({
    queryKey: ['reminders', 'due'],
    queryFn: reminderApi.getDue,
    refetchInterval: 30_000, // poll every 30s
  })

  const markDelivered = useMutation({
    mutationFn: reminderApi.markDelivered,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reminders'] }),
  })

  const createReminder = useMutation({
    mutationFn: ({
      task_id,
      remind_at,
      message,
    }: {
      task_id: number
      remind_at: string
      message: string
    }) => reminderApi.create(task_id, remind_at, message),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reminders'] }),
  })

  return { dueReminders, markDelivered, createReminder }
}
