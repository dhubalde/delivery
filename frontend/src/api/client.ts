import axios from 'axios'
import { useAuthStore } from '@/stores/auth.store'

export const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE || '/api' })

function extractPublicSlug(url?: string): string | null {
  if (!url) return null
  // match /public/<slug>/...  or /public/<slug>
  const m = url.match(/\/public\/([^\/\?#]+)/)
  if (m && m[1]) return decodeURIComponent(m[1])
  return null
}

function getCustomerAccessForSlug(slug: string): string | null {
  try {
    const raw = localStorage.getItem(`customer:${slug}`)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (parsed?.tokens) return parsed.tokens.access || parsed.access || null
    return parsed?.access || null
  } catch {
    return null
  }
}

api.interceptors.request.use((cfg) => {
  const auth = useAuthStore()
  const publicSlug = extractPublicSlug(cfg.url || '')
  const isPublic = !!publicSlug
  if (!isPublic && auth.access) {
    cfg.headers.Authorization = `Bearer ${auth.access}`
  } else if (isPublic) {
    // For public endpoints, attach Customer JWT if available for this slug
    const customerAccess = publicSlug ? getCustomerAccessForSlug(publicSlug) : null
    if (customerAccess) {
      // Only for orders and customers/me we need Customer header; catalog is AllowAny without auth but sending it is harmless
      // For orders/me, Customer header is required to link/auth; for other public GETs we can still send but not required
      if (cfg.url?.includes('/orders') || cfg.url?.includes('/customers/')) {
        cfg.headers.Authorization = `Customer ${customerAccess}`
      } else {
        // For catalog/products/categories/flavors we don't need auth, but if token exists we don't auto-attach to keep AllowAny simple
        // Do not set Authorization for read-only public catalog
      }
    } else {
      // Guest: ensure no Bearer leaks to public endpoint (AllowAny)
      if ((cfg.headers.Authorization as string | undefined)?.startsWith('Bearer ')) {
        delete cfg.headers.Authorization
      }
    }
    // If caller explicitly set Customer header (e.g., fetchMe with manual header), respect it
    // Our logic above already respects explicit Customer if we didn't overwrite
  } else if (auth.access) {
    // Fallback for non-public already handled
  }
  if (cfg.method && ['post', 'patch', 'put'].includes(cfg.method)) {
    cfg.headers['Idempotency-Key'] = crypto.randomUUID()
  }
  if (cfg.url?.includes('/v1/')) {
    let slug = auth.merchantSlug || localStorage.getItem('merchantSlug') || 'ice-zone'
    if (slug === 'zona-ice') slug = 'ice-zone'
    const p = cfg.params as Record<string, unknown> | undefined
    if (!p?.merchant_slug) cfg.params = { ...p, merchant_slug: slug }
    if (!cfg.headers['X-Merchant-Slug'] && !cfg.headers['x-merchant-slug']) cfg.headers['X-Merchant-Slug'] = slug
  }
  return cfg
})

let refreshPromise: Promise<string> | null = null

api.interceptors.response.use(
  (r) => r,
  async (err) => {
    const { response, config } = err
    const status = response?.status
    if (status === 401 && !config._retry) {
      config._retry = true
      const auth = useAuthStore()
      if (!refreshPromise) {
        refreshPromise = axios
          .post(`${api.defaults.baseURL}/auth/token/refresh`, { refresh: auth.refresh })
          .then((res) => {
            auth.setTokens(res.data.access, res.data.refresh ?? auth.refresh)
            return res.data.access as string
          })
          .catch((e) => {
            auth.clear()
            window.location.href = '/login'
            throw e
          })
          .finally(() => { refreshPromise = null })
      }
      const token = await refreshPromise
      config.headers.Authorization = `Bearer ${token}`
      return api(config)
    }
    if (status === 403) {
      const serverMsg = response?.data?.error?.message
      const msg = serverMsg || 'Permiso denegado'
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg, type: 'error' } }))
      console.warn('[403]', response.data)
    }
    if (status === 409) {
      const code = response?.data?.error?.code
      const serverMsg = response?.data?.error?.message
      const msg = serverMsg || (code === 'INVALID_TRANSITION' ? 'Transición no válida — refetch' : (code ?? 'Conflicto'))
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg, type: 'warning' } }))
      return Promise.reject(err)
    }
    if (status === 400 || status === 422) return Promise.reject(err)
    if (status >= 500) {
      const serverMsg = response?.data?.error?.message || response?.data?.detail || response?.data?.error || null
      const msg = serverMsg ? String(serverMsg) : 'Error de servidor'
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg, type: 'error' } }))
      console.error('[500]', response.data)
    }
    if (!response && err.code === 'ERR_NETWORK') {
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg: 'Sin conexión', type: 'warning' } }))
    }
    return Promise.reject(err)
  },
)
