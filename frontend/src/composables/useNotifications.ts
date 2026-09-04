import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, ref } from 'vue'
import { api } from '@/api/client'

type NotificationRaw = {
  id: number
  merchant: number
  recipient_type: string
  recipient_name: string
  order: number | null
  order_code: number
  message: string
  type: string
  type_label: string
  recipient_type_label: string
  is_read: boolean
  created_at: string
}

export function useNotifications(options?: { recipientType?: 'CUSTOMER' | 'EMPLOYEE' }) {
  const qc = useQueryClient()
  const unreadOnly = ref(false)
  const recipientType = options?.recipientType

  const { data, isLoading, error } = useQuery({
    queryKey: ['notifications', { unread: unreadOnly.value, recipientType }],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (unreadOnly.value) params.unread = 'true'
      if (recipientType) params.recipient_type = recipientType
      const { data } = await api.get('/v1/notifications/', {
        params,
      })
      return (Array.isArray(data) ? data : (data.results ?? data.items ?? data)) as NotificationRaw[]
    },
    staleTime: 0,
    refetchInterval: 10000,
    refetchOnWindowFocus: true,
  })

  const notifications = computed(() => (data.value ?? []) as NotificationRaw[])

  const unreadCount = computed(() => notifications.value.filter((n) => !n.is_read).length)

  const markRead = useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post(`/v1/notifications/${id}/mark-read/`)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const markAllRead = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/v1/notifications/mark-all-read/')
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const remove = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/v1/notifications/${id}/delete/`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  return {
    notifications,
    unreadCount,
    isLoading,
    error,
    unreadOnly,
    markRead,
    markAllRead,
    remove,
  }
}