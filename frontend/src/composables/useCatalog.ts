import { useQuery } from '@tanstack/vue-query'
import { computed, unref } from 'vue'
import { api } from '@/api/client'
import type { Ref } from 'vue'

type MaybeRef<T> = T | Ref<T>

type MerchantInfo = {
  id: number
  slug: string
  name: string
  is_active: boolean
  logo_url: string | null
}

type CatalogAggregate = {
  merchant: MerchantInfo
  categories: unknown[]
  products: unknown[]
  flavors: unknown[]
  stats: { visit_count: number; buyer_count: number }
}

export function useCatalog(slug: MaybeRef<string>) {
  const query = useQuery({
    queryKey: computed(() => ['catalog', 'aggregate', unref(slug)] as const),
    queryFn: async () => {
      const s = unref(slug)
      const { data } = await api.get(`/public/${s}/catalog`)
      return data as CatalogAggregate
    },
    staleTime: 15_000,
    gcTime: 60_000,
    refetchOnWindowFocus: false,
    retry: false,
  })
  return query
}
