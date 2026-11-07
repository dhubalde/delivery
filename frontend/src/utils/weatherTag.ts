export type WeatherTag = { label: string; color: string; icon: string }

export function getWeatherTag(tempMax: number, condition?: string): WeatherTag | null {
  const c = (condition ?? '').toLowerCase()
  if (c.includes('rain') || c.includes('lluvia') || c.includes('tormenta')) {
    return { label: 'Día lluvioso', color: 'blue-grey', icon: 'mdi-weather-rainy' }
  }
  if (tempMax >= 28) return { label: 'Día caluroso', color: 'deep-orange', icon: 'mdi-weather-sunny' }
  if (tempMax >= 24) return { label: 'Día cálido', color: 'orange', icon: 'mdi-weather-partly-cloudy' }
  if (tempMax <= 14) return { label: 'Día frío', color: 'blue', icon: 'mdi-weather-snowy' }
  if (tempMax <= 18) return { label: 'Día fresco', color: 'indigo', icon: 'mdi-weather-cloudy' }
  return { label: 'Día templado', color: 'teal', icon: 'mdi-weather-sunny' }
}
