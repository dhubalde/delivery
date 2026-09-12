import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { api } from '@/api/client'

export const MY_ORDERS_KEY = 'myOrders'
export const MY_ORDERS_PREFIX = 'myOrders:'

export function myOrdersKey(slug: string): string {
  return `${MY_ORDERS_PREFIX}${slug}`
}

function resolveSlugForStorage(explicit?: string): string | null {
  if (explicit) return explicit
  try {
    // try to infer from current location path /:slug/...
    const path = window.location?.pathname || ''
    const m = path.match(/^\/([^\/]+)/)
    if (m && m[1] && !['panel', 'master', 'login', 'change-password', 'api'].includes(m[1])) {
      return m[1]
    }
  } catch {}
  return null
}

type MyOrder = {
  id: number
  code: number
  state: string
  total: string
  business_date: string
  created_at?: string | null
  updated_at?: string | null
}

export function getMyOrderIds(slug?: string): number[] {
  const targetSlug = resolveSlugForStorage(slug)
  const key = targetSlug ? myOrdersKey(targetSlug) : MY_ORDERS_KEY
  // fallback: if no slug resolved, try legacy key + slug-aware keys? For migration, merge both
  try {
    const raw = localStorage.getItem(key)
    if (!raw && !targetSlug) return []
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter((v: unknown) => typeof v === 'number' && Number.isFinite(v))
  } catch {
    return []
  }
}

export function getMyOrderIdsForSlug(slug: string): number[] {
  try {
    const raw = localStorage.getItem(myOrdersKey(slug))
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter((v: unknown) => typeof v === 'number' && Number.isFinite(v))
  } catch {
    return []
  }
}

export function addMyOrderId(id: number, slug?: string): void {
  const targetSlug = resolveSlugForStorage(slug)
  const key = targetSlug ? myOrdersKey(targetSlug) : MY_ORDERS_KEY
  try {
    const ids = targetSlug ? getMyOrderIdsForSlug(targetSlug) : getMyOrderIds()
    if (!ids.includes(id)) {
      ids.unshift(id)
      localStorage.setItem(key, JSON.stringify(ids.slice(0, 20)))
      window.dispatchEvent(new CustomEvent('myOrders:updated'))
    }
  } catch {}
}

export function addMyOrderIdForSlug(id: number, slug: string): void {
  try {
    const ids = getMyOrderIdsForSlug(slug)
    if (!ids.includes(id)) {
      ids.unshift(id)
      localStorage.setItem(myOrdersKey(slug), JSON.stringify(ids.slice(0, 20)))
      window.dispatchEvent(new CustomEvent('myOrders:updated'))
    }
  } catch {}
}

export function removeMyOrderId(id: number, slug?: string): void {
  const targetSlug = resolveSlugForStorage(slug)
  const key = targetSlug ? myOrdersKey(targetSlug) : MY_ORDERS_KEY
  try {
    const ids = (targetSlug ? getMyOrderIdsForSlug(targetSlug) : getMyOrderIds()).filter((v) => v !== id)
    localStorage.setItem(key, JSON.stringify(ids))
    window.dispatchEvent(new CustomEvent('myOrders:updated'))
  } catch {}
}

export function removeMyOrderIdForSlug(id: number, slug: string): void {
  try {
    const ids = getMyOrderIdsForSlug(slug).filter((v) => v !== id)
    localStorage.setItem(myOrdersKey(slug), JSON.stringify(ids))
    window.dispatchEvent(new CustomEvent('myOrders:updated'))
  } catch {}
}

function useMyOrderIdsReactive(slug?: string) {
  const initial = slug ? getMyOrderIdsForSlug(slug) : getMyOrderIds()
  const ids = ref<number[]>(initial)
  const refresh = () => {
    ids.value = slug ? getMyOrderIdsForSlug(slug) : getMyOrderIds()
  }
  const onCustom = () => refresh()
  const onStorage = (e: StorageEvent) => {
    const targetKey = slug ? myOrdersKey(slug) : null
    if (!targetKey) {
      if (e.key === MY_ORDERS_KEY || (e.key && e.key.startsWith(MY_ORDERS_PREFIX))) refresh()
    } else {
      if (e.key === targetKey) refresh()
    }
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

export function useMyOrders(slug?: string | import('vue').Ref<string | undefined>) {
  const slugVal = computed(() => {
    const raw = slug ? (typeof slug === 'string' ? slug : (slug as import('vue').Ref<string | undefined>).value) : undefined
    if (raw) return raw
    try {
      const path = window.location?.pathname || ''
      const m = path.match(/^\/([^\/]+)/)
      if (m && m[1] && !['panel', 'master', 'login', 'change-password', 'api'].includes(m[1])) return m[1]
    } catch {}
    return undefined
  })
  const { ids, refresh } = useMyOrderIdsReactive(slugVal.value)
  const query = useQuery({
    queryKey: computed(() => ['myOrders', slugVal.value || 'default', ids.value] as const),
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
    refetchInterval: 15_000,
    staleTime: 10_000,
    gcTime: 60_000,
    refetchOnWindowFocus: false,
    refetchIntervalInBackground: false,
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
