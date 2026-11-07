import { defineStore } from 'pinia'
import { api } from '@/api/client'

export function customerKey(slug: string): string {
  return `customer:${slug}`
}

type CustomerProfile = {
  id: number
  email: string | null
  phone: string
  name: string
  default_address: string
  merchant_slug: string
  merchant_id: number
  merchant?: string
}

type CustomerTokens = {
  access: string
  refresh: string
}

type StoredCustomer = {
  access: string
  refresh: string
  profile: CustomerProfile | null
}

function readStored(slug: string): StoredCustomer | null {
  try {
    const raw = localStorage.getItem(customerKey(slug))
    if (!raw) return null
    const parsed = JSON.parse(raw)
    // support legacy shape where tokens nested
    if (parsed?.tokens) {
      return {
        access: parsed.tokens.access || parsed.access || '',
        refresh: parsed.tokens.refresh || parsed.refresh || '',
        profile: parsed.customer || parsed.profile || null,
      }
    }
    return {
      access: parsed?.access || '',
      refresh: parsed?.refresh || '',
      profile: parsed?.profile || parsed?.customer || null,
    }
  } catch {
    return null
  }
}

function writeStored(slug: string, data: StoredCustomer): void {
  try {
    localStorage.setItem(customerKey(slug), JSON.stringify(data))
  } catch {}
}

export const useCustomerStore = defineStore('customer', {
  state: () => ({
    _slug: '' as string,
    access: '' as string,
    refresh: '' as string,
    profile: null as CustomerProfile | null,
    _hydratedSlug: '' as string,
  }),
  getters: {
    isAuthenticated: (s) => !!s.access,
    displayName: (s) => s.profile?.name || '',
  },
  actions: {
    hydrate(slug: string): void {
      if (this._hydratedSlug === slug) return
      const stored = readStored(slug)
      this._slug = slug
      this._hydratedSlug = slug
      if (stored) {
        this.access = stored.access
        this.refresh = stored.refresh
        this.profile = stored.profile
      } else {
        this.access = ''
        this.refresh = ''
        this.profile = null
      }
    },
    setSlug(slug: string): void {
      this.hydrate(slug)
    },
    persist(): void {
      if (!this._slug) return
      writeStored(this._slug, {
        access: this.access,
        refresh: this.refresh,
        profile: this.profile,
      })
    },
    clearMemory(): void {
      this.access = ''
      this.refresh = ''
      this.profile = null
    },
    logout(slug?: string): void {
      const target = slug || this._slug
      if (target) {
        try {
          localStorage.removeItem(customerKey(target))
        } catch {}
      }
      if (!slug || slug === this._slug) {
        this.clearMemory()
      }
    },
    async register(slug: string, payload: { email: string; phone: string; name: string; address: string; password: string }): Promise<StoredCustomer> {
      const { data } = await api.post(`/public/${slug}/customers/register`, payload)
      const access: string = data?.access || data?.tokens?.access || ''
      const refresh: string = data?.refresh || data?.tokens?.refresh || ''
      const profile: CustomerProfile | null = data?.customer || null
      this._slug = slug
      this._hydratedSlug = slug
      this.access = access
      this.refresh = refresh
      this.profile = profile
      this.persist()
      return { access, refresh, profile }
    },
    async login(slug: string, payload: { email: string; password: string }): Promise<StoredCustomer> {
      const { data } = await api.post(`/public/${slug}/customers/login`, payload)
      const access: string = data?.access || data?.tokens?.access || ''
      const refresh: string = data?.refresh || data?.tokens?.refresh || ''
      const profile: CustomerProfile | null = data?.customer || null
      this._slug = slug
      this._hydratedSlug = slug
      this.access = access
      this.refresh = refresh
      this.profile = profile
      this.persist()
      return { access, refresh, profile }
    },
    async fetchMe(slug: string): Promise<CustomerProfile | null> {
      this.hydrate(slug)
      if (!this.access) return null
      try {
        const { data } = await api.get(`/public/${slug}/customers/me`, {
          headers: { Authorization: `Customer ${this.access}` },
        })
        // API returns {id, email, phone, name, default_address, merchant_slug, ...}
        const profile: CustomerProfile = {
          id: data.id,
          email: data.email ?? null,
          phone: data.phone,
          name: data.name,
          default_address: data.default_address ?? '',
          merchant_slug: data.merchant_slug || data.merchant || slug,
          merchant_id: data.merchant_id,
          merchant: data.merchant || data.merchant_slug,
        }
        this.profile = profile
        this.persist()
        return profile
      } catch {
        return null
      }
    },
    async updateProfile(slug: string, payload: { name?: string; phone?: string; default_address?: string }): Promise<CustomerProfile | null> {
      this.hydrate(slug)
      if (!this.access) return null
      const { data } = await api.patch(`/public/${slug}/customers/me`, payload, {
        headers: { Authorization: `Customer ${this.access}` },
      })
      const profile: CustomerProfile = {
        id: data.id,
        email: data.email ?? this.profile?.email ?? null,
        phone: data.phone,
        name: data.name,
        default_address: data.default_address ?? '',
        merchant_slug: data.merchant_slug || slug,
        merchant_id: data.merchant_id,
      }
      this.profile = profile
      this.persist()
      return profile
    },
    getAccessForSlug(slug: string): string | null {
      const stored = readStored(slug)
      return stored?.access || null
    },
  },
})

export function getCustomerAccessForSlug(slug: string): string | null {
  const stored = readStored(slug)
  return stored?.access || null
}
