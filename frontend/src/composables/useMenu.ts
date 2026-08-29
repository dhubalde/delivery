import { useQuery } from '@tanstack/vue-query'
import { computed, unref } from 'vue'
import { api } from '@/api/client'
import { qk } from '@/queries/keys'
import { INTERVALS } from '@/queries/intervals'
import type { Ref } from 'vue'
export function useMenu(slug: string | Ref<string>) {
  return useQuery({
    queryKey: computed(() => qk.menu(unref(slug))),
    queryFn: async () => {
      const s = unref(slug)
      const { data } = await api.get(`/public/${s}/menu`)
      return data as { is_open?: boolean; closed?: boolean; next_open_at?: string | null; isOpen?: boolean }
    },
    refetchInterval: INTERVALS.CATALOG,
    staleTime: 0,
  })
}
