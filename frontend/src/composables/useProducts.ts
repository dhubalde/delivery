import { useQuery } from '@tanstack/vue-query'
import { computed, unref } from 'vue'
import { api } from '@/api/client'
import { qk } from '@/queries/keys'
import { INTERVALS } from '@/queries/intervals'
import type { Ref } from 'vue'

type MaybeRef<T> = T | Ref<T>

export function useProducts(slug: MaybeRef<string>, category: MaybeRef<number | undefined>, search: MaybeRef<string | undefined>) {
  const query = useQuery({
    queryKey: computed(() => qk.products({ slug: unref(slug), category: unref(category), search: unref(search) || undefined })),
    queryFn: async () => {
      const s = unref(slug)
      const c = unref(category)
      const q = unref(search)
      const params: Record<string, string> = {}
      if (c) params.category = String(c)
      if (q) params.search = q
      try {
        const { data } = await api.get(`/public/${s}/products`, { params })
        return (Array.isArray(data) ? data : data.results ?? data.items ?? []) as unknown[]
      } catch (e: any) {
        if (e?.response?.status === 404) {
          const fallbackParams: Record<string, string> = { ...params, merchant_slug: s }
          const { data } = await api.get(`/catalog/products/`, { params: fallbackParams })
          return (Array.isArray(data) ? data : data.results ?? data.items ?? []) as unknown[]
        }
        throw e
      }
    },
    refetchInterval: INTERVALS.CATALOG,
    staleTime: 0,
  })
  return query
}

export function useFlavors(slug: MaybeRef<string>, category: MaybeRef<number | undefined>, search: MaybeRef<string | undefined>) {
  const query = useQuery({
    queryKey: computed(() => qk.flavors({ slug: unref(slug), category: unref(category), search: unref(search) || undefined })),
    queryFn: async () => {
      const s = unref(slug)
      const c = unref(category)
      const q = unref(search)
      const params: Record<string, string> = {}
      if (c) params.category = String(c)
      if (q) params.search = q
      try {
        const { data } = await api.get(`/public/${s}/flavors`, { params })
        return (Array.isArray(data) ? data : data.results ?? data.items ?? []) as unknown[]
      } catch (e: any) {
        if (e?.response?.status === 404) {
          const fallbackParams: Record<string, string> = { ...params, merchant_slug: s }
          const { data } = await api.get(`/catalog/flavors/`, { params: fallbackParams })
          return (Array.isArray(data) ? data : data.results ?? data.items ?? []) as unknown[]
        }
        throw e
      }
    },
    refetchInterval: INTERVALS.CATALOG,
    staleTime: 0,
  })
  return query
}
