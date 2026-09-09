import { api } from '../client'

export type OperativeRole = 'ADMIN' | 'CAJERO' | 'PREPARADOR' | 'REPARTIDOR' | 'TOMA_PEDIDOS'
export type UserKind = 'PERSONAL' | 'STATION'
export type AppUser = {
  id: number; username: string; role: OperativeRole; kind: UserKind
  sector?: string | null; branch?: { id: number; name: string } | null
  is_active: boolean; must_change_password: boolean; merchant_id?: number
}
export type UserCreate = {
  username: string; password: string; role: OperativeRole
  kind?: UserKind; sector?: string | null; branch_id?: number | null
}
const unwrap = (d: unknown) => Array.isArray(d) ? d as AppUser[] : ((d as { results?: AppUser[] }).results ?? d as AppUser)
export const usersApi = {
  list: async () => unwrap((await api.get('/v1/users/')).data) as AppUser[],
  create: async (b: UserCreate) => (await api.post('/v1/users/', b)).data as AppUser,
  update: async (id: number, b: Partial<UserCreate & { is_active: boolean }>) => (await api.patch(`/v1/users/${id}/`, b)).data as AppUser,
  remove: async (id: number) => (await api.delete(`/v1/users/${id}/`)).data,
  changePassword: async (b: { current_password: string; new_password: string }) => (await api.post('/v1/users/change-password/', b)).data,
  resetRequest: async (username: string) => (await api.post('/v1/users/reset-request/', { username })).data as { reset_token: string },
  resetConfirm: async (b: { token: string; new_password: string }) => (await api.post('/v1/users/reset-confirm/', b)).data,
}
