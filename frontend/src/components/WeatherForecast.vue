<template>
  <v-card class="mb-4" elevation="1" data-testid="weather-forecast">
    <v-card-title class="d-flex align-center justify-space-between text-subtitle-2">
      <span><v-icon size="small" class="mr-1">mdi-weather-cloudy</v-icon>Pronóstico</span>
      <v-chip v-if="isDemo" size="x-small" color="secondary" variant="tonal">demo</v-chip>
      <v-chip v-else size="x-small" color="primary" variant="tonal">live</v-chip>
    </v-card-title>
    <v-divider />
    <v-card-text class="pa-2">
      <div class="d-flex ga-2 w-100 mx-0 px-0 ma-0 pa-0" style="display:flex;gap:8px;width:100%;margin:0;padding:0;box-sizing:border-box">
        <v-card v-for="d in days" :key="d.date" variant="tonal" class="pa-2 text-center flex-grow-1 ma-0" style="flex:1 1 0;min-width:0;width:100%;margin:0;box-sizing:border-box">
          <div class="text-caption font-weight-bold">{{ formatWeekday(d.date) }}</div>
          <div class="text-caption">{{ formatDate(d.date) }}</div>
          <v-icon :icon="d.icon" size="28" color="primary" class="my-1" />
          <div class="text-caption">{{ d.condition }}</div>
          <div class="text-caption"><span class="font-weight-bold">{{ d.tempMax }}°</span> / {{ d.tempMin }}°</div>
          <v-chip v-if="tagFor(d)" :color="tagFor(d)!.color" size="x-small" variant="tonal" class="mt-1">{{ tagFor(d)!.label }}</v-chip>
        </v-card>
      </div>
      <div v-if="isLoading && days.length === 0" class="d-flex justify-center mt-2"><v-progress-circular indeterminate size="20" /></div>
      <div v-if="isError" class="text-caption text-warning mt-2">Pronóstico demo — reintentando live <v-btn size="x-small" variant="text" @click="() => refetch()">Reintentar</v-btn></div>
    </v-card-text>
  </v-card>
</template>
<script setup lang="ts">
// API chain: 1) GET /api/v1/weather/forecast?days=5 2) OpenWeatherMap (VITE_WEATHER_KEY) 3) mock local
import { useForecast } from '@/composables/useForecast'
import { getWeatherTag } from '@/utils/weatherTag'
const { days, isDemo, isLoading, isError, refetch } = useForecast()
function tagFor(d: { tempMax: number; condition: string }) {
  return getWeatherTag(d.tempMax, d.condition)
}
function formatWeekday(raw: string): string {
  if (/^\d{4}-\d{2}-\d{2}/.test(raw)) {
    const dt = new Date(raw + 'T12:00:00')
    if (!isNaN(dt.getTime())) {
      const wd = dt.toLocaleDateString('es-AR', { weekday: 'short' })
      return wd.charAt(0).toUpperCase() + wd.slice(1).replace('.', '')
    }
  }
  return raw
}
function formatDate(raw: string): string {
  if (/^\d{4}-\d{2}-\d{2}/.test(raw)) {
    const dt = new Date(raw + 'T12:00:00')
    if (!isNaN(dt.getTime())) return dt.toLocaleDateString('es-AR')
  }
  const dt = new Date(raw)
  if (!isNaN(dt.getTime()) && raw.includes('/')) return raw
  return raw
}
</script>
