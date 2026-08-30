import { useQuery } from '@tanstack/vue-query'
import { computed } from 'vue'
import { qk } from '@/queries/keys'
import { INTERVALS } from '@/queries/intervals'
import { api } from '@/api/client'

export type ForecastDay = { date: string; tempMin: number; tempMax: number; condition: string; icon: string }

function isoDate(offsetDays: number): string {
  const d = new Date()
  d.setDate(d.getDate() + offsetDays)
  return d.toISOString().slice(0, 10)
}

const MOCK: ForecastDay[] = [
  { date: isoDate(0), tempMin: 18, tempMax: 26, condition: 'Soleado', icon: 'mdi-weather-sunny' },
  { date: isoDate(1), tempMin: 16, tempMax: 24, condition: 'Parcial', icon: 'mdi-weather-partly-cloudy' },
  { date: isoDate(2), tempMin: 15, tempMax: 22, condition: 'Nublado', icon: 'mdi-weather-cloudy' },
  { date: isoDate(3), tempMin: 14, tempMax: 20, condition: 'Lluvia', icon: 'mdi-weather-rainy' },
  { date: isoDate(4), tempMin: 17, tempMax: 25, condition: 'Soleado', icon: 'mdi-weather-sunny' },
  { date: isoDate(5), tempMin: 19, tempMax: 27, condition: 'Soleado', icon: 'mdi-weather-sunny' },
]

function genMockFallback(): ForecastDay[] {
  const conds: ForecastDay[] = []
  for (let i = 0; i < 6; i++) {
    const tMax = 20 + Math.round(Math.random() * 8)
    const tMin = tMax - 6 - Math.round(Math.random() * 3)
    const icons = ['mdi-weather-sunny', 'mdi-weather-partly-cloudy', 'mdi-weather-cloudy', 'mdi-weather-rainy']
    const condNames = ['Soleado', 'Parcial', 'Nublado', 'Lluvia']
    const idx = Math.floor(Math.random() * 4)
    conds.push({ date: isoDate(i), tempMin: tMin, tempMax: tMax, condition: condNames[idx], icon: icons[idx] })
  }
  return conds
}

function owmIconToMdi(icon: string): string {
  const map: Record<string, string> = {
    '01d': 'mdi-weather-sunny',
    '01n': 'mdi-weather-night',
    '02d': 'mdi-weather-partly-cloudy',
    '02n': 'mdi-weather-night-partly-cloudy',
    '03d': 'mdi-weather-cloudy',
    '03n': 'mdi-weather-cloudy',
    '04d': 'mdi-weather-cloudy',
    '04n': 'mdi-weather-cloudy',
    '09d': 'mdi-weather-rainy',
    '09n': 'mdi-weather-rainy',
    '10d': 'mdi-weather-pouring',
    '10n': 'mdi-weather-pouring',
    '11d': 'mdi-weather-lightning',
    '11n': 'mdi-weather-lightning',
    '13d': 'mdi-weather-snowy',
    '13n': 'mdi-weather-snowy',
    '50d': 'mdi-weather-fog',
    '50n': 'mdi-weather-fog',
  }
  return map[icon] ?? 'mdi-weather-cloudy'
}

const LS_KEY = 'ice-zone-forecast'
const TTL = INTERVALS.WEATHER

function loadCache(): { at: number; data: ForecastDay[] } | null {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as { at: number; data: ForecastDay[] }
    if (Date.now() - parsed.at > TTL) return null
    if (!Array.isArray(parsed.data) || parsed.data.length < 5) return null
    return parsed
  } catch { return null }
}

function saveCache(data: ForecastDay[]) {
  try { localStorage.setItem(LS_KEY, JSON.stringify({ at: Date.now(), data })) } catch { /* ignore */ }
}

/**
 * API chain: 1) GET /api/v1/weather/forecast?days=6 (backend propio) -> live
 *            2) OpenWeatherMap https://api.openweathermap.org/data/2.5/forecast con VITE_WEATHER_KEY -> live
 *               Usa lat/lon si VITE_WEATHER_LAT/LON están seteados (-34.61,-58.38 CABA), sino q=VITE_WEATHER_CITY
 *            3) Mock local con fechas ISO (isoDate) -> demo
 */
async function fetchForecast(): Promise<{ data: ForecastDay[]; isDemo: boolean }> {
  const cached = loadCache()
  if (cached) return { data: cached.data, isDemo: true }
  try {
    const res = await api.get('/v1/weather/forecast', { params: { days: 6 } })
    const d = res.data as ForecastDay[] | { data?: ForecastDay[]; results?: ForecastDay[]; days?: ForecastDay[] }
    const arr = Array.isArray(d) ? d : (d as { data?: ForecastDay[] }).data ?? (d as { results?: ForecastDay[] }).results ?? (d as { days?: ForecastDay[] }).days ?? null
    if (Array.isArray(arr) && arr.length >= 5) {
      const mapped: ForecastDay[] = arr.slice(0, 6).map((x: ForecastDay) => ({
        date: x.date, tempMin: Math.round(x.tempMin), tempMax: Math.round(x.tempMax), condition: x.condition, icon: x.icon || 'mdi-weather-cloudy',
      }))
      saveCache(mapped)
      return { data: mapped, isDemo: false }
    }
    throw new Error('invalid payload')
  } catch {
    const key = import.meta.env.VITE_WEATHER_KEY as string | undefined
    if (key) {
      try {
        const city = (import.meta.env.VITE_WEATHER_CITY as string | undefined) || 'Buenos Aires'
        const lat = import.meta.env.VITE_WEATHER_LAT as string | undefined
        const lon = import.meta.env.VITE_WEATHER_LON as string | undefined
        const base = 'https://api.openweathermap.org/data/2.5/forecast'
        const url = lat && lon
          ? `${base}?lat=${lat}&lon=${lon}&units=metric&lang=es&appid=${key}`
          : `${base}?q=${encodeURIComponent(city)}&units=metric&lang=es&appid=${key}`
        const res = await fetch(url)
        if (!res.ok) throw new Error(String(res.status))
        const j = await res.json() as { list: { dt_txt: string; main: { temp_min: number; temp_max: number }; weather: { main: string; description: string; icon: string }[] }[] }
        const byDay = new Map<string, { min: number; max: number; cond: string; icon: string }>()
        for (const e of j.list) {
          const d = e.dt_txt.slice(0, 10)
          const w = e.weather[0]
          const cond = w?.description ? w.description.charAt(0).toUpperCase() + w.description.slice(1) : (w?.main ?? '')
          const mdi = w?.icon ? owmIconToMdi(w.icon) : 'mdi-weather-cloudy'
          if (!byDay.has(d)) byDay.set(d, { min: e.main.temp_min, max: e.main.temp_max, cond, icon: mdi })
          else {
            const cur = byDay.get(d)!
            cur.min = Math.min(cur.min, e.main.temp_min)
            cur.max = Math.max(cur.max, e.main.temp_max)
          }
        }
        const mapped: ForecastDay[] = [...byDay.entries()].slice(0, 6).map(([date, v]) => ({ date, tempMin: Math.round(v.min), tempMax: Math.round(v.max), condition: v.cond, icon: v.icon }))
        if (mapped.length >= 5) { saveCache(mapped); return { data: mapped, isDemo: false } }
      } catch { /* fallback to mock */ }
    }
    const fallback = MOCK.length === 6 ? MOCK : genMockFallback()
    saveCache(fallback)
    return { data: fallback, isDemo: true }
  }
}

export function useForecast() {
  const q = useQuery({
    queryKey: qk.forecast({ days: 6 }),
    queryFn: fetchForecast,
    staleTime: TTL,
    gcTime: TTL * 2,
    refetchInterval: TTL,
    retry: 1,
  })
  const days = computed(() => {
    const d = q.data.value?.data
    return d && Array.isArray(d) && d.length >= 5 ? d : MOCK
  })
  const isDemo = computed(() => q.data.value?.isDemo ?? true)
  return { ...q, days, isDemo }
}
