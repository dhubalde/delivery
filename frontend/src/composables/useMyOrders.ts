import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { api } from '@/api/client'

export const MY_ORDERS_KEY = 'myOrders'

type MyOrder = {
  id: number
  code: number
  state: string
  total: string
  business_date: string
  created_at?: string | null
  updated_at?: string | null
}

export function getMyOrderIds(): number[] {
  try {
    const raw = localStorage.getItem(MY_ORDERS_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter((v: unknown) => typeof v === 'number' && Number.isFinite(v))
  } catch {
    return []
  }
}

export function addMyOrderId(id: number): void {
  try {
    const ids = getMyOrderIds()
    if (!ids.includes(id)) {
      ids.unshift(id)
      localStorage.setItem(MY_ORDERS_KEY, JSON.stringify(ids.slice(0, 20)))
      window.dispatchEvent(new CustomEvent('myOrders:updated'))
    }
  } catch {}
}

export function removeMyOrderId(id: number): void {
  try {
    const ids = getMyOrderIds().filter((v) => v !== id)
    localStorage.setItem(MY_ORDERS_KEY, JSON.stringify(ids))
    window.dispatchEvent(new CustomEvent('myOrders:updated'))
  } catch {}
}

function useMyOrderIdsReactive() {
  const ids = ref<number[]>(getMyOrderIds())
  const refresh = () => {
    ids.value = getMyOrderIds()
  }
  const onCustom = () => refresh()
  const onStorage = (e: StorageEvent) => {
    if (e.key === MY_ORDERS_KEY) refresh()
  }
  onMounted(() => {
    window.addEventListener('myOrders:updated', onCustom as EventListener)
    window.addEventListener('storage', onStorage)
  })
  onUnmounted(() => {
    window.removeEventListener('myOrders:updated', onCustom as EventListener)
    window.removeEventListener('storage', onStorage)
  })
  return { ids, refresh }
}

export function useMyOrders() {
  const { ids, refresh } = useMyOrderIdsReactive()
  const query = useQuery({
    queryKey: computed(() => ['myOrders', ids.value] as const),
    queryFn: async () => {
      const list = ids.value
      if (list.length === 0) return [] as MyOrder[]
      const results = await Promise.allSettled(
        list.map(async (orderId) => {
          const { data } = await api.get(`/v1/orders/${orderId}`)
          return data as MyOrder
        })
      )
      const orders: MyOrder[] = []
      for (const r of results) {
        if (r.status === 'fulfilled' && r.value) orders.push(r.value)
      }
      return orders.sort((a, b) => {
        const da = a.created_at ? Date.parse(a.created_at) : 0
        const db = b.created_at ? Date.parse(b.created_at) : 0
        return db - da
      })
    },
    refetchInterval: 5000,
    staleTime: 0,
    enabled: computed(() => ids.value.length > 0),
  })
  return { ...query, ids, refresh }
}

export const useOrdersPublic = useMyOrders

export function useCancelMyOrder() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post(`/v1/orders/${id}/transition`, { to_state: 'CANCELADO' })
      return data as MyOrder
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['myOrders'] })
      await qc.invalidateQueries({ queryKey: ['orders', 'board'] })
    },
    onError: (err: unknown) => {
      const response = (err as { response?: { status?: number; data?: { error?: { code?: string; message?: string } } } })?.response
      const status = response?.status
      const serverMsg = response?.data?.error?.message
      if (status === 409) {
        window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg: serverMsg || 'El pedido ya no se puede anular', type: 'warning' } }))
      } else if (status === 404) {
        window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg: 'Pedido no encontrado', type: 'error' } }))
      }
    },
  })
}
