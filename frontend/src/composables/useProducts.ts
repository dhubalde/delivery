import { useQuery } from '@tanstack/vue-query'
import { computed, unref } from 'vue'
import { api } from '@/api/client'
import { qk } from '@/queries/keys'
import { INTERVALS } from '@/queries/intervals'
import type { Ref } from 'vue'

type MaybeRef<T> = T | Ref<T>

export function useCategories(slug: MaybeRef<string>) {
  const query = useQuery({
    queryKey: computed(() => qk.categories({ slug: unref(slug) })),
    queryFn: async () => {
      const s = unref(slug)
      const { data } = await api.get(`/public/${s}/categories`)
      return (Array.isArray(data) ? data : (data as any).results ?? (data as any).items ?? data) as unknown[]
    },
    refetchInterval: INTERVALS.CATALOG,
    staleTime: 0,
  })
  return query
}

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
      const { data } = await api.get(`/public/${s}/products`, { params })
      return (Array.isArray(data) ? data : data.results ?? data.items ?? []) as unknown[]
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
      const { data } = await api.get(`/public/${s}/flavors`, { params })
      return (Array.isArray(data) ? data : data.results ?? data.items ?? []) as unknown[]
    },
    refetchInterval: INTERVALS.CATALOG,
    staleTime: 0,
  })
  return query
}
