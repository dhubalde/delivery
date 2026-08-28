import { useQuery } from '@tanstack/vue-query'
import { computed } from 'vue'
import { qk } from '@/queries/keys'
import { INTERVALS } from '@/queries/intervals'

export type ForecastDay = { date: string; tempMin: number; tempMax: number; condition: string; icon: string }

const MOCK: ForecastDay[] = [
  { date: 'Hoy', tempMin: 18, tempMax: 26, condition: 'Soleado', icon: 'mdi-weather-sunny' },
  { date: 'Mañana', tempMin: 16, tempMax: 24, condition: 'Parcial', icon: 'mdi-weather-partly-cloudy' },
  { date: 'Mié', tempMin: 15, tempMax: 22, condition: 'Nublado', icon: 'mdi-weather-cloudy' },
  { date: 'Jue', tempMin: 14, tempMax: 20, condition: 'Lluvia', icon: 'mdi-weather-rainy' },
  { date: 'Vie', tempMin: 17, tempMax: 25, condition: 'Soleado', icon: 'mdi-weather-sunny' },
]

const LS_KEY = 'ice-zone-forecast'
const TTL = INTERVALS.WEATHER

function loadCache(): { at: number; data: ForecastDay[] } | null {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as { at: number; data: ForecastDay[] }
    if (Date.now() - parsed.at > TTL) return null
    return parsed
  } catch { return null }
}

function saveCache(data: ForecastDay[]) {
  try { localStorage.setItem(LS_KEY, JSON.stringify({ at: Date.now(), data })) } catch { /* ignore */ }
}

async function fetchForecast(): Promise<{ data: ForecastDay[]; isDemo: boolean }> {
  const cached = loadCache()
  if (cached) return { data: cached.data, isDemo: true }
  const key = import.meta.env.VITE_WEATHER_KEY as string | undefined
  if (!key) {
    saveCache(MOCK)
    return { data: MOCK, isDemo: true }
  }
  try {
    const res = await fetch(`https://api.openweathermap.org/data/2.5/forecast?cnt=40&units=metric&lang=es&appid=${key}&q=Buenos%20Aires,ar`)
    if (!res.ok) throw new Error(String(res.status))
    const j = await res.json() as { list: { dt_txt: string; main: { temp_min: number; temp_max: number }; weather: { main: string; icon: string }[] }[] }
    const byDay = new Map<string, { min: number; max: number; cond: string; icon: string }>()
    for (const e of j.list) {
      const d = e.dt_txt.slice(0, 10)
      if (!byDay.has(d)) byDay.set(d, { min: e.main.temp_min, max: e.main.temp_max, cond: e.weather[0]?.main ?? '', icon: 'mdi-weather-cloudy' })
      else {
        const cur = byDay.get(d)!
        cur.min = Math.min(cur.min, e.main.temp_min)
        cur.max = Math.max(cur.max, e.main.temp_max)
      }
    }
    const mapped: ForecastDay[] = [...byDay.values()].slice(0, 5).map((v, i) => ({ date: i === 0 ? 'Hoy' : i === 1 ? 'Mañana' : `D+${i}`, tempMin: Math.round(v.min), tempMax: Math.round(v.max), condition: v.cond, icon: v.icon }))
    const data = mapped.length === 5 ? mapped : MOCK
    saveCache(data)
    return { data, isDemo: false }
  } catch {
    saveCache(MOCK)
    return { data: MOCK, isDemo: true }
  }
}

export function useForecast() {
  const q = useQuery({
    queryKey: qk.forecast({ days: 5 }),
    queryFn: fetchForecast,
    staleTime: TTL,
    gcTime: TTL * 2,
    refetchInterval: TTL,
    retry: 1,
  })
  const days = computed(() => q.data.value?.data ?? MOCK)
  const isDemo = computed(() => q.data.value?.isDemo ?? true)
  return { ...q, days, isDemo }
}
