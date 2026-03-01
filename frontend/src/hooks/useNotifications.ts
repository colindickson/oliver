import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationApi, type Notification } from '../api/client'

export function useNotifications() {
  const qc = useQueryClient()
  const [shownIds, setShownIds] = useState<Set<number>>(new Set())

  const { data: unreadNotifications = [] } = useQuery({
    queryKey: ['notifications', 'unread'],
    queryFn: notificationApi.getUnread,
    refetchInterval: 15_000,
  })

  const markRead = useMutation({
    mutationFn: notificationApi.markRead,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })

  const popupNotification: Notification | null =
    unreadNotifications.find(n => !shownIds.has(n.id)) ?? null

  const markPopupShown = (id: number) =>
    setShownIds(prev => new Set(prev).add(id))

  const unreadCount = unreadNotifications.length

  return { popupNotification, markPopupShown, unreadNotifications, markRead, unreadCount }
}
