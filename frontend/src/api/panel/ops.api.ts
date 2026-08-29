import { api } from '@/api/client'
export type Schedule = { id: number; weekday: number; time_ranges: { opens_at: string; closes_at: string }[] }
export type SpecialDate = { id: number; date: string; is_closed: boolean; reason: string }
export type DeliveryConfig = { id: number; modo: 'PROPIO'|'TERCERIZADO'|'AMBOS'; cobro: 'EN_PEDIDO'|'EN_ENTREGA'|'AMBOS'; calculo: 'POR_ZONA'|'FIJO'|'GRATIS_MONTO'|'POR_DISTANCIA'; flat_amount: string|null; free_threshold: string|null; third_party_fixed_amount: string|null }
export type Zone = { id: number; name: string; base_fee: string }
const unwrap = (d: unknown) => Array.isArray(d) ? d as never[] : ((d as { results?: never[]; items?: never[] }).results ?? (d as { items?: never[] }).items ?? d as never[])
export const schedulesApi = {
  list: async () => unwrap((await api.get('/v1/schedules/')).data) as Schedule[],
  upsert: async (b: { weekday: number; ranges: { opens_at: string; closes_at: string }[] }) => (await api.put('/v1/schedules/', b)).data as Schedule,
  remove: async (id: number) => (await api.delete(`/v1/schedules/${id}/`)).data,
}
export const specialDatesApi = {
  list: async () => unwrap((await api.get('/v1/special-dates/')).data) as SpecialDate[],
  create: async (b: Partial<SpecialDate>) => (await api.post('/v1/special-dates/', b)).data as SpecialDate,
  update: async (id: number, b: Partial<SpecialDate>) => (await api.put(`/v1/special-dates/${id}/`, b)).data as SpecialDate,
  remove: async (id: number) => (await api.delete(`/v1/special-dates/${id}/`)).data,
}
export const deliveryApi = {
  get: async () => (await api.get('/v1/delivery-config/')).data as DeliveryConfig,
  update: async (b: Partial<DeliveryConfig>) => (await api.put('/v1/delivery-config/', b)).data as DeliveryConfig,
}
export const zonesApi = {
  list: async () => unwrap((await api.get('/v1/zones/')).data) as Zone[],
  create: async (b: Partial<Zone>) => (await api.post('/v1/zones/', b)).data as Zone,
  update: async (id: number, b: Partial<Zone>) => (await api.put(`/v1/zones/${id}/`, b)).data as Zone,
  remove: async (id: number) => (await api.delete(`/v1/zones/${id}/`)).data,
}
