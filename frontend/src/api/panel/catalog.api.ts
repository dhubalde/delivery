import { api } from '@/api/client'
export type Category = { id: number; name: string; position: number; is_active: boolean }
export type Product = { id: number; category_id: number; name: string; product_type: 'POTE'|'UNIT'; pote_size: 'KG_1'|'KG_HALF'|'KG_QUARTER'|null; min_flavors: number|null; max_flavors: number|null; price: string; is_active: boolean }
export type Flavor = { id: number; name: string; category_id: number|null; is_active: boolean }
const unwrap = (d: unknown) => Array.isArray(d) ? d as never[] : ((d as { results?: never[]; items?: never[] }).results ?? (d as { items?: never[] }).items ?? d as never[])
export const catalogApi = {
  categories: {
    list: async () => unwrap((await api.get('/v1/categories')).data) as Category[],
    create: async (b: Partial<Category>) => (await api.post('/v1/categories', b)).data as Category,
    update: async (id: number, b: Partial<Category>) => (await api.put(`/v1/categories/${id}`, b)).data as Category,
    remove: async (id: number) => (await api.delete(`/v1/categories/${id}`)).data,
  },
  products: {
    list: async (p?: { category?: number; search?: string }) => unwrap((await api.get('/v1/products', { params: p })).data) as Product[],
    create: async (b: Partial<Product>) => (await api.post('/v1/products', b)).data as Product,
    update: async (id: number, b: Partial<Product>) => (await api.put(`/v1/products/${id}`, b)).data as Product,
    remove: async (id: number) => (await api.delete(`/v1/products/${id}`)).data,
  },
  flavors: {
    list: async (p?: { category?: number; search?: string }) => unwrap((await api.get('/v1/flavors', { params: p })).data) as Flavor[],
    create: async (b: Partial<Flavor>) => (await api.post('/v1/flavors', b)).data as Flavor,
    update: async (id: number, b: Partial<Flavor>) => (await api.put(`/v1/flavors/${id}`, b)).data as Flavor,
    remove: async (id: number) => (await api.delete(`/v1/flavors/${id}`)).data,
  },
}
