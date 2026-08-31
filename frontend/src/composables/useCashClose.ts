import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { qk } from '@/queries/keys'
import { cashApi } from '@/api/panel/cash.api'
import type { Ref } from 'vue'
import { computed, unref } from 'vue'
export const cashErrStatus = (e: unknown) => (e as { response?: { status?: number } })?.response?.status
export const cashErrCode = (e: unknown) => (e as { response?: { data?: { error?: { code?: string } } } })?.response?.data?.error?.code ?? ''
export const cashErrMsg = (e: unknown) => (e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message ?? 'Error'
export function useCashPreview(businessDate?: Ref<string> | string) {
  const normalized = computed(() => {
    const v = unref(businessDate as never) as string | undefined
    return v ?? undefined
  })
  return useQuery({
    queryKey: computed(() => qk.adminCashPreview(normalized.value)),
    queryFn: () => cashApi.preview(normalized.value),
    retry: false,
  })
}
export function useCloseCash() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: cashApi.close as never,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'cashPreview'] }),
  })
}
