import axios from 'axios'
import { useAuthStore } from '@/stores/auth.store'

export const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE || '/api' })

api.interceptors.request.use((cfg) => {
  const auth = useAuthStore()
  if (auth.access) cfg.headers.Authorization = `Bearer ${auth.access}`
  if (cfg.method && ['post', 'patch', 'put'].includes(cfg.method)) {
    cfg.headers['Idempotency-Key'] = crypto.randomUUID()
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
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg: 'Permiso denegado', type: 'error' } }))
      console.warn('[403]', response.data)
    }
    if (status === 409) {
      const code = response?.data?.error?.code
      const msg = code === 'INVALID_TRANSITION' ? 'Transición no válida — refetch' : (code ?? 'Conflicto')
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg, type: 'warning' } }))
      return Promise.reject(err)
    }
    if (status === 400 || status === 422) return Promise.reject(err)
    if (status >= 500) {
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg: 'Error del servidor — reintentando', type: 'error' } }))
      console.error('[500]', response.data)
    }
    if (!response && err.code === 'ERR_NETWORK') {
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg: 'Sin conexión', type: 'warning' } }))
    }
    return Promise.reject(err)
  },
)
