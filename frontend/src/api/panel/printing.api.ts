import { api } from '@/api/client'

export type TicketItem = { product_name: string; quantity: number; unit_price: string; line_total: string; flavors: string[] }
export type TicketPayment = { method: string; status: string; amount: string }
export type TicketOrder = {
  id: number
  code: number
  state: string
  business_date: string
  created_at?: string | null
  customer_name: string
  customer_phone: string
  address: string
  fulfillment: string
  source: string
  items_total: string
  delivery_fee: string
  discount: string
  total: string
  items: TicketItem[]
  payments: TicketPayment[]
}
export type PrintJob = {
  id: number
  created_at: string | null
  printed_at: string | null
  printed_count: number
  order: TicketOrder
}

export const printingApi = {
  pending: async (): Promise<PrintJob[]> => (await api.get('/v1/print-jobs/')).data as PrintJob[],
  markPrinted: async (id: number): Promise<PrintJob> =>
    (await api.post(`/v1/print-jobs/${id}/printed/`)).data as PrintJob,
}
