import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, unref } from 'vue'
import type { Ref } from 'vue'
import { api } from '@/api/client'
import { qk } from '@/queries/keys'
import { INTERVALS } from '@/queries/intervals'

type Order = { id: number; code: string; state: string; fulfillment: string; cash_declared: boolean; total: string; payments: { method: string; status: string }[]; customer_name?: string }
type MaybeRef<T> = T | Ref<T>

export function useOrdersBoard(state: MaybeRef<string>, businessDate: MaybeRef<string>) {
  return useQuery({
    queryKey: computed(() => qk.ordersBoard({ state: unref(state), businessDate: unref(businessDate) })),
    queryFn: async () => {
      const s = unref(state)
      const d = unref(businessDate)
      const { data } = await api.get('/v1/orders', { params: { state: s, business_date: d } })
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
    mutationFn: async ({ id, to_state }: { id: number; to_state: string }) => {
      const { data } = await api.post(`/v1/orders/${id}/transition`, { to_state })
      return data
    },
    onMutate: async ({ id, to_state }) => {
      await qc.cancelQueries({ queryKey: ['orders', 'board'] })
      const snapshots = qc.getQueriesData<Order[]>({ queryKey: ['orders', 'board'] })
      const map = new Map(JSON.stringify(snapshots) ? snapshots : [])
      for (const [key, list] of snapshots) {
        if (!Array.isArray(list)) continue
        const idx = list.findIndex((o) => o.id === id)
        if (idx !== -1) {
          const next = [...list]
          const [moved] = next.splice(idx, 1)
          qc.setQueryData(key, next)
          void moved
          void to_state
        }
      }
      return { snapshots }
    },
    onError: (err: unknown, _vars, ctx) => {
      if (ctx?.snapshots) {
        for (const [key, data] of ctx.snapshots as [readonly unknown[], unknown][]) qc.setQueryData(key as unknown[], data as never)
      }
      const status = (err as { response?: { status?: number; data?: { error?: { code?: string; message?: string } } } })?.response?.status
      const code = (err as { response?: { data?: { error?: { code?: string } } } })?.response?.data?.error?.code
      if (status === 409) {
        const msg = code === 'INVALID_TRANSITION' ? 'Estado ya cambió' : (code ?? 'Transición no válida')
        console.warn(`[409] ${msg}`)
      }
      if (status === 403) console.warn('[403] Permiso denegado')
      if (status === 401) window.location.href = '/login'
    },
    onSettled: async (_data, _err, vars) => {
      await qc.invalidateQueries({ queryKey: ['orders', 'board'] })
      void vars
    },
  })
}
