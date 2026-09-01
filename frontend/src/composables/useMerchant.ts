import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { qk } from '@/queries/keys'
import { merchantApi } from '@/api/panel/merchant.api'

export function useMerchant() {
  return useQuery({ queryKey: qk.merchant(), queryFn: merchantApi.get })
}

export function usePublicMerchant(slug?: string) {
  return useQuery({ queryKey: qk.publicMerchant(slug), queryFn: () => merchantApi.getPublic(slug) })
}

export function useUpdateMerchant() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: merchantApi.update as never,
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.merchant() }),
  })
}

export function useUploadMerchantLogo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: merchantApi.uploadLogo as never,
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.merchant() }),
  })
}
