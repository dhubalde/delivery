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
    staleTime: 15_000,
    gcTime: 60_000,
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: false,
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
      let slug: string | null = null;
      try {
        const path = window.location?.pathname || "";
        const m = path.match(/^\/([^/]+)/);
        if (m && m[1] && !["panel", "master", "login", "change-password", "api"].includes(m[1])) slug = m[1];
      } catch {
        slug = null;
      }
      if (!slug) {
        try {
          slug = localStorage.getItem("merchantSlug") || "ice-zone";
        } catch {
          slug = "ice-zone";
        }
      }
      if (slug === "zona-ice") slug = "ice-zone";
      await api.delete(`/v1/notifications/${id}/delete/`, {
        params: { merchant_slug: slug },
      });
      return id;
    },
    onMutate: async (id: number) => {
      await qc.cancelQueries({ queryKey: ["notifications"] });
      const previous = qc.getQueriesData({ queryKey: ["notifications"] });
      (qc as unknown as { setQueriesData: (f: unknown, u: (old: unknown) => unknown) => void }).setQueriesData(
        { queryKey: ["notifications"] },
        (old: unknown) => {
          if (Array.isArray(old)) return (old as NotificationRaw[]).filter((n) => n.id !== id);
          if (old && typeof old === "object" && Array.isArray((old as { results?: unknown }).results))
            return { ...(old as Record<string, unknown>), results: ((old as { results: NotificationRaw[] }).results).filter((n) => n.id !== id) };
          return old;
        },
      );
      return { previous };
    },
    onError: (err, _id, context) => {
      const previous = (context as { previous?: [unknown, unknown][] } | undefined)?.previous;
      if (previous) for (const [key, data] of previous) (qc as unknown as { setQueryData: (k: unknown, d: unknown) => void }).setQueryData(key, data);
      const status = (err as { response?: { status?: number } })?.response?.status;
      window.dispatchEvent(
        new CustomEvent("app:toast", {
          detail: { msg: status === 404 ? "Ya estaba eliminada" : "No se pudo eliminar", type: "error" },
        }),
      );
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
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