import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, unref } from 'vue'
import type { Ref } from 'vue'
import { api } from '@/api/client'
import { qk } from '@/queries/keys'
import { INTERVALS } from '@/queries/intervals'

type Order = { id: number; code: string; state: string; fulfillment: string; cash_declared: boolean; total: string; payments: { method: string; status: string }[]; customer_name?: string }
type MaybeRef<T> = T | Ref<T>

export function useOrdersBoard(state: MaybeRef<string>, businessDate: MaybeRef<string>, endDate?: MaybeRef<string>) {
  const normalizedEnd = computed(() => {
    const v = unref(endDate as never) as string | undefined
    return v ?? undefined
  })
  return useQuery({
    queryKey: computed(() => {
      const params = { state: unref(state), businessDate: unref(businessDate) }
      if (normalizedEnd.value) (params as { endDate?: string }).endDate = normalizedEnd.value
      return qk.ordersBoard(params)
    }),
    queryFn: async () => {
      const s = unref(state)
      const d = unref(businessDate)
      const params: Record<string, string> = { state: s, business_date: d }
      if (normalizedEnd.value) params.business_date_to = normalizedEnd.value
      const { data } = await api.get('/v1/orders', { params })
      return (Array.isArray(data) ? data : (data.results ?? data.items ?? data)) as Order[]
    },
    refetchInterval: INTERVALS.BOARD,
    staleTime: 0,
    refetchOnWindowFocus: true,
  })
}

export function useTransition() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, to_state, reason }: { id: number; to_state: string; reason?: string }) => {
      const payload: Record<string, string> = { to_state }
      if (reason) payload.reason = reason
      const { data } = await api.post(`/v1/orders/${id}/transition`, payload)
      return data
    },
    onMutate: async ({ id }) => {
      await qc.cancelQueries({ queryKey: ['orders', 'board'] })
      const snapshots = qc.getQueriesData<Order[]>({ queryKey: ['orders', 'board'] })
      for (const [key, list] of snapshots) {
        if (!Array.isArray(list)) continue
        const idx = list.findIndex((o) => o.id === id)
        if (idx !== -1) {
          const next = [...list]
          next.splice(idx, 1)
          qc.setQueryData(key, next)
        }
      }
      return { snapshots }
    },
    onError: (err: unknown, _vars, ctx) => {
      if (ctx?.snapshots) {
        for (const [key, data] of ctx.snapshots as [readonly unknown[], unknown][]) qc.setQueryData(key as unknown[], data as never)
      }
      const response = (err as { response?: { status?: number; data?: { error?: { code?: string; message?: string } } } })?.response
      const status = response?.status
      const code = response?.data?.error?.code
      const serverMsg = response?.data?.error?.message
      if (status === 409) {
        const msg = serverMsg || (code === 'INVALID_TRANSITION' ? 'Estado ya cambió' : (code ?? 'Transición no válida'))
        window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg, type: 'warning' } }))
        console.warn(`[409] ${msg}`)
      } else if (status === 403) {
        const msg = serverMsg || 'Permiso denegado'
        window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg, type: 'error' } }))
        console.warn('[403] Permiso denegado')
      } else if (status && status >= 500) {
        const msg = serverMsg || 'Error de servidor'
        window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg, type: 'error' } }))
        console.error(`[${status}] ${msg}`)
      }
      if (status === 401) window.location.href = '/login'
    },
    onSettled: async () => {
      await qc.invalidateQueries({ queryKey: ['orders', 'board'] })
    },
  })
}
