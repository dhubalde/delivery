import { api } from '@/api/client'
export type Category = { id: number; name: string; position: number; is_active: boolean }
export type Product = { id: number; category_id: number; name: string; product_type: 'POTE'|'UNIT'; pote_size: 'KG_1'|'KG_HALF'|'KG_QUARTER'|null; min_flavors: number|null; max_flavors: number|null; price: string; is_active: boolean }
export type Flavor = { id: number; name: string; category_id: number|null; is_active: boolean }
const unwrap = (d: unknown) => Array.isArray(d) ? d as never[] : ((d as { results?: never[]; items?: never[] }).results ?? (d as { items?: never[] }).items ?? d as never[])
export const catalogApi = {
  categories: {
    list: async () => {
      try { return unwrap((await api.get('/catalog/categories/')).data) as Category[] } catch (e: unknown) {
        const s = (e as { response?: { status?: number } })?.response?.status
        if (s === 404 || s === 405) return unwrap((await api.get('/public/ice-zone/categories/')).data) as Category[]
        throw e
      }
    },
    create: async (b: Partial<Category>) => (await api.post('/catalog/categories/', b)).data as Category,
    update: async (id: number, b: Partial<Category>) => (await api.put(`/catalog/categories/${id}/`, b)).data as Category,
    remove: async (id: number) => (await api.delete(`/catalog/categories/${id}/`)).data,
  },
  products: {
    list: async (p?: { category?: number; search?: string }) => unwrap((await api.get('/catalog/products/', { params: p })).data) as Product[],
    create: async (b: Partial<Product> & { flavor_ids?: number[] }) => (await api.post('/catalog/products/', b)).data as Product,
    update: async (id: number, b: Partial<Product> & { flavor_ids?: number[] }) => (await api.put(`/catalog/products/${id}/`, b)).data as Product,
    remove: async (id: number) => (await api.delete(`/catalog/products/${id}/`)).data,
  },
  flavors: {
    list: async (p?: { category?: number; search?: string }) => {
      try { return unwrap((await api.get('/catalog/flavors/', { params: p })).data) as Flavor[] } catch {
        return unwrap((await api.get('/public/ice-zone/flavors/', { params: p })).data) as Flavor[]
      }
    },
    create: async (b: Partial<Flavor>) => (await api.post('/catalog/flavors/', b)).data as Flavor,
    update: async (id: number, b: Partial<Flavor>) => (await api.put(`/catalog/flavors/${id}/`, b)).data as Flavor,
    remove: async (id: number) => (await api.delete(`/catalog/flavors/${id}/`)).data,
  },
}
