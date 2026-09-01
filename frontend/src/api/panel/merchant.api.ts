import { api } from '@/api/client'

export type Merchant = {
  id: number
  name: string
  slug: string
  vertical: string
  is_active: boolean
  logo: string | null
  logo_url: string | null
}

export const merchantApi = {
  get: async () => (await api.get('/v1/merchant/')).data as Merchant,
  getPublic: async (slug?: string) => (await api.get('/v1/merchant/public/', { params: slug ? { slug } : {} })).data as Merchant,
  update: async (payload: Partial<Pick<Merchant, 'name' | 'logo_url'>>) =>
    (await api.patch('/v1/merchant/', payload)).data as Merchant,
  uploadLogo: async (file: File) => {
    const fd = new FormData()
    fd.append('logo', file)
    return (await api.post('/v1/merchant/logo/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })).data as Merchant
  },
  setLogoUrl: async (logo_url: string) => (await api.post('/v1/merchant/logo/', { logo_url })).data as Merchant,
}
