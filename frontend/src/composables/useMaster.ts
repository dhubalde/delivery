import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { masterApi } from '@/api/panel/master.api'

export const masterCompaniesKey = ['master', 'companies']
export const masterUsersKey = ['master', 'users']
export const masterAuditKey = ['master', 'audit']

export function useMasterCompanies() {
  return useQuery({ queryKey: masterCompaniesKey, queryFn: masterApi.companies })
}
export function useMasterUsers() {
  const qc = useQueryClient()
  const q = useQuery({ queryKey: masterUsersKey, queryFn: masterApi.internalUsers })
  const inv = () => {
    qc.invalidateQueries({ queryKey: masterUsersKey })
    qc.invalidateQueries({ queryKey: masterAuditKey })
  }
  const onboardM = useMutation({
    mutationFn: masterApi.onboard,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: masterCompaniesKey })
      qc.invalidateQueries({ queryKey: masterAuditKey })
    },
  })
  const createM = useMutation({ mutationFn: masterApi.createInternal, onSuccess: inv })
  const updateM = useMutation({
    mutationFn: (v: { id: number; role?: string; assigned_merchants?: number[]; is_active?: boolean }) =>
      masterApi.updateInternal(v.id, v),
    onSuccess: inv,
  })
  return { q, onboardM, createM, updateM }
}
export function useMasterAudit() {
  return useQuery({ queryKey: masterAuditKey, queryFn: masterApi.audit, refetchInterval: 15000 })
}
