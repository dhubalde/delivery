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
    if (status === 403) console.warn('[403]', response.data)
    if (status === 409) return Promise.reject(err)
    if (status >= 500) console.error('[500]', response.data)
    return Promise.reject(err)
  },
)
