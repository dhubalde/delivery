import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { usersApi, type AppUser, type UserCreate } from '@/api/panel/users.api'

export const usersKey = ['admin', 'users']
export function useAdminUsers() {
  const qc = useQueryClient()
  const q = useQuery({ queryKey: usersKey, queryFn: usersApi.list, refetchInterval: 15000 })
  const inv = () => qc.invalidateQueries({ queryKey: usersKey })
  const createM = useMutation({ mutationFn: usersApi.create, onSuccess: inv })
  const updateM = useMutation({
    mutationFn: (v: { id: number } & Partial<UserCreate & { is_active: boolean }>) =>
      usersApi.update(v.id, v),
    onSuccess: inv,
  })
  const removeM = useMutation({ mutationFn: usersApi.remove, onSuccess: inv })
  return { q, createM, updateM, removeM }
}
export function userErrDetails(e: unknown): Record<string, string> {
  const d = (e as { response?: { data?: unknown } })?.response?.data as Record<string, unknown> | undefined
  if (!d || typeof d !== 'object') return {}
  const out: Record<string, string> = {}
  for (const [k, v] of Object.entries(d)) out[k] = Array.isArray(v) ? String(v[0]) : String(v)
  return out
}
export type { AppUser }
