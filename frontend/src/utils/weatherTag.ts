export type WeatherTag = { label: string; color: string; icon: string }

export function getWeatherTag(tempMax: number, condition?: string): WeatherTag | null {
  const c = (condition ?? '').toLowerCase()
  if (c.includes('rain') || c.includes('lluvia') || c.includes('tormenta')) {
    return { label: 'Día lluvioso — promo para casa', color: 'blue-grey', icon: 'mdi-weather-rainy' }
  }
  if (tempMax >= 28) return { label: 'Día caluroso — ideal helado', color: 'deep-orange', icon: 'mdi-weather-sunny' }
  if (tempMax >= 24) return { label: 'Día cálido — perfecto para pote', color: 'orange', icon: 'mdi-weather-partly-cloudy' }
  if (tempMax <= 14) return { label: 'Día frío — helado intenso', color: 'blue', icon: 'mdi-weather-snowy' }
  if (tempMax <= 18) return { label: 'Día fresco — antojo helado', color: 'indigo', icon: 'mdi-weather-cloudy' }
  return { label: 'Día templado — ideal helado', color: 'teal', icon: 'mdi-weather-sunny' }
}
