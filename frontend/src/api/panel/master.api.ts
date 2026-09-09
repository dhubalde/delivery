import { api } from '../client'

export type Company = {
  id: number; name: string; slug: string
  seat_limit: number; has_branches: boolean; is_active: boolean
}
export type InternalUser = {
  id: number; username: string; role: string
  assigned_merchants: { id: number; name: string; slug: string }[]
  is_active: boolean; must_change_password: boolean
}
export type AuditEntry = {
  id: number; actor: string | null; action: string
  merchant: string | null; detail: Record<string, unknown>; created_at: string
}
const unwrap = <T,>(d: unknown): T[] => Array.isArray(d) ? d as T[] : (((d as { results?: T[] }).results ?? []) as T[])
export const masterApi = {
  companies: async () => unwrap<Company>((await api.get('/master/companies/')).data),
  onboard: async (b: { name: string; slug: string; logo_url?: string; seat_limit: number; has_branches: boolean; admin_username: string; admin_password: string }) =>
    (await api.post('/master/companies/', b)).data,
  internalUsers: async () => unwrap<InternalUser>((await api.get('/master/users/')).data),
  createInternal: async (b: { username: string; password: string; role: string; assigned_merchants?: number[] }) =>
    (await api.post('/master/users/', b)).data as InternalUser,
  updateInternal: async (id: number, b: { role?: string; assigned_merchants?: number[]; is_active?: boolean }) =>
    (await api.patch(`/master/users/${id}/`, b)).data as InternalUser,
  audit: async () => unwrap<AuditEntry>((await api.get('/master/audit/')).data),
  resetRequest: async (username: string) =>
    (await api.post('/master/users/reset-request/', { username })).data as { reset_token: string },
  sessions: async (username: string) =>
    (((await api.get('/master/sessions/', { params: { username } })).data) ?? []) as { jti_prefix: string; created_at: string; active: boolean }[],
  revokeSessions: async (username: string) =>
    (await api.post('/master/sessions/revoke/', { username })).data as { revoked: number },
}
