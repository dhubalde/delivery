import { api } from '@/api/client'
export type CashPreview = { totals: { EFECTIVO: string; BILLETERAS_VIRTUALES: string; TARJETAS: string; TOTAL_ENTREGADOS: number; TOTAL_RECHAZADOS: number }; ticket_payload: Record<string, unknown>; already_closed?: boolean; business_date?: string }
export type CashClosure = CashPreview & { id: number; business_date: string }
export const cashApi = {
  preview: async (businessDate?: string, businessDateTo?: string) => {
    const params: Record<string, string> = {}
    if (businessDate) params.business_date = businessDate
    if (businessDateTo) params.business_date_to = businessDateTo
    const { data } = await api.get('/v1/cash/close/', { params })
    return data as CashPreview
  },
  close: async () => (await api.post('/v1/cash/close/')).data as CashClosure,
}
