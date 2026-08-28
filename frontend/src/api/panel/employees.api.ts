import { api } from '@/api/client'
export const ROLES = ['ADMIN','CAJERO','PREPARADOR','REPARTIDOR','TOMA_PEDIDOS'] as const
export type Role = typeof ROLES[number]
export type Employee = { id: number; display_name: string; is_active: boolean; merchant: number; roles: Role[] }
const unwrap = (d: unknown) => Array.isArray(d) ? d as Employee[] : ((d as { results?: Employee[] }).results ?? (d as { items?: Employee[] }).items ?? d as Employee)
export const employeesApi = {
  list: async () => unwrap((await api.get('/v1/employees')).data) as Employee[],
  create: async (b: { display_name: string; is_active: boolean; roles: Role[] }) => (await api.post('/v1/employees', b)).data as Employee,
  update: async (id: number, b: Partial<{ display_name: string; is_active: boolean; roles: Role[] }>) => (await api.put(`/v1/employees/${id}`, b)).data as Employee,
  remove: async (id: number) => (await api.delete(`/v1/employees/${id}`)).data,
}
