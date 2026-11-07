<template>
  <div class="address-map-picker">
    <v-text-field
      v-model="query"
      label="Buscar dirección"
      placeholder="Ej: San Martín 1234, Santa Fe"
      density="compact"
      :loading="searching"
      :error-messages="searchError"
      clearable
      @keyup.enter="search"
    >
      <template #append-inner>
        <v-btn icon="mdi-magnify" size="small" variant="text" :loading="searching" @click="search" aria-label="Buscar" />
      </template>
    </v-text-field>

    <v-list v-if="results.length" density="compact" class="mb-2 results-list">
      <v-list-item
        v-for="r in results"
        :key="`${r.lat},${r.lon}`"
        :title="shortLabel(r)"
        :subtitle="r.display_name"
        @click="pickResult(r)"
      >
        <template #prepend><v-icon icon="mdi-map-marker" /></template>
      </v-list-item>
    </v-list>

    <div ref="mapEl" class="map" />

    <div class="text-caption text-medium-emphasis mt-2">
      Tocá el mapa o arrastrá el pin para ajustar la ubicación.
    </div>
    <v-chip v-if="displayName" size="small" variant="tonal" class="mt-1 chip-address">
      <v-icon icon="mdi-map-marker-check" start />{{ displayName }}
    </v-chip>
    <div v-if="reverseError" class="text-caption text-error mt-1">{{ reverseError }}</div>

    <div class="d-flex ga-2 mt-3">
      <v-btn variant="text" @click="$emit('cancel')">Cancelar</v-btn>
      <v-spacer />
      <v-btn color="primary" :disabled="!hasFix" :loading="resolving" @click="confirm">
        Confirmar ubicación
      </v-btn>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Default center: Santa Fe, Argentina.
const DEFAULT_LAT = -31.6333
const DEFAULT_LNG = -60.7
const DEFAULT_ZOOM = 14

export interface MapAddress {
  lat: number
  lng: number
  display_name: string
}

interface NominatimResult {
  lat: string
  lon: string
  display_name: string
  address?: Record<string, string>
}

const props = withDefaults(
  defineProps<{
    lat?: number | null
    lng?: number | null
    addressHint?: string
  }>(),
  { lat: null, lng: null, addressHint: '' },
)

const emit = defineEmits<{
  (e: 'confirm', value: MapAddress): void
  (e: 'cancel'): void
}>()

const mapEl = ref<HTMLElement | null>(null)
const query = ref(props.addressHint || '')
const results = ref<NominatimResult[]>([])
const searching = ref(false)
const searchError = ref('')
const displayName = ref('')
const hasFix = ref(false)
const resolving = ref(false)
const reverseError = ref('')

let map: L.Map | null = null
let marker: L.Marker | null = null
let debounceTimer: ReturnType<typeof setTimeout> | null = null

function pinIcon(): L.DivIcon {
  return L.divIcon({
    className: 'addr-pin-wrapper',
    html: '<div class="addr-pin"></div>',
    iconSize: [28, 28],
    iconAnchor: [14, 26],
  })
}

function currentLatLng(): { lat: number; lng: number } {
  if (marker) {
    const p = marker.getLatLng()
    return { lat: p.lat, lng: p.lng }
  }
  return { lat: props.lat ?? DEFAULT_LAT, lng: props.lng ?? DEFAULT_LNG }
}

/** Build a short, human-friendly address; fall back to display_name. */
function formatAddress(data: { display_name: string; address?: Record<string, string> }): string {
  const a = data.address || {}
  const road = a.road || a.pedestrian || a.footway || ''
  const number = a.house_number || ''
  const city = a.city || a.town || a.village || a.municipality || a.county || ''
  const state = a.state || ''
  if (road) {
    const street = number ? `${road} ${number}` : road
    const tail = [city, state].filter(Boolean).join(', ')
    return tail ? `${street}, ${tail}` : street
  }
  return data.display_name
}

function scheduleReverse(): void {
  hasFix.value = true
  reverseError.value = ''
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => void reverseGeocode(), 600)
}

async function reverseGeocode(): Promise<void> {
  const { lat, lng } = currentLatLng()
  try {
    const url =
      `https://nominatim.openstreetmap.org/reverse?format=jsonv2` +
      `&lat=${lat}&lon=${lng}&accept-language=es`
    const res = await fetch(url, { headers: { Accept: 'application/json' } })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = (await res.json()) as NominatimResult
    displayName.value = formatAddress(data)
  } catch {
    reverseError.value = 'No se pudo obtener la dirección de ese punto. Probá de nuevo.'
  }
}

async function search(): Promise<void> {
  const q = query.value.trim()
  if (!q || !map) return
  searching.value = true
  searchError.value = ''
  results.value = []
  try {
    const url =
      `https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1` +
      `&limit=5&countrycodes=ar&accept-language=es&q=${encodeURIComponent(q)}`
    const res = await fetch(url, { headers: { Accept: 'application/json' } })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = (await res.json()) as NominatimResult[]
    results.value = data
    if (!data.length) searchError.value = 'Sin resultados. Probá con calle y altura.'
  } catch {
    searchError.value = 'Error al buscar. Revisá tu conexión.'
  } finally {
    searching.value = false
  }
}

function shortLabel(r: NominatimResult): string {
  return formatAddress(r)
}

function pickResult(r: NominatimResult): void {
  const lat = Number(r.lat)
  const lng = Number(r.lon)
  if (!map || Number.isNaN(lat) || Number.isNaN(lng)) return
  map.setView([lat, lng], 16)
  marker?.setLatLng([lat, lng])
  displayName.value = formatAddress(r)
  hasFix.value = true
  results.value = []
}

function movePin(e: L.LeafletMouseEvent): void {
  marker?.setLatLng(e.latlng)
  scheduleReverse()
}

function confirm(): void {
  const { lat, lng } = currentLatLng()
  resolving.value = true
  try {
    emit('confirm', { lat, lng, display_name: displayName.value || `${lat.toFixed(5)}, ${lng.toFixed(5)}` })
  } finally {
    resolving.value = false
  }
}

onMounted(() => {
  if (!mapEl.value) return
  const startLat = props.lat ?? DEFAULT_LAT
  const startLng = props.lng ?? DEFAULT_LNG
  map = L.map(mapEl.value).setView([startLat, startLng], props.lat != null ? 16 : DEFAULT_ZOOM)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map)
  marker = L.marker([startLat, startLng], { draggable: true, icon: pinIcon() }).addTo(map)
  marker.on('dragend', scheduleReverse)
  map.on('click', movePin)
  // Resolve the initial address so Confirm is enabled right away.
  void reverseGeocode().then(() => {
    hasFix.value = true
  })
  // Fix tiles when the dialog animates open with a zero-size container.
  setTimeout(() => map?.invalidateSize(), 300)
})

onBeforeUnmount(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
  map?.off('click', movePin)
  map?.remove()
  map = null
  marker = null
})
</script>

<style scoped>
.map {
  height: 320px;
  width: 100%;
  border-radius: 8px;
  z-index: 0;
}
.results-list {
  max-height: 180px;
  overflow-y: auto;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
}
.chip-address {
  max-width: 100%;
  height: auto;
  white-space: normal;
}
.chip-address :deep(.v-chip__content) {
  white-space: normal;
}
@media (max-width: 600px) {
  .map {
    height: 260px;
  }
}
</style>

<style>
.addr-pin-wrapper {
  background: transparent;
  border: none;
}
.addr-pin {
  width: 22px;
  height: 22px;
  border-radius: 50% 50% 50% 0;
  transform: rotate(-45deg);
  background: #1867c0;
  border: 3px solid #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
}
</style>
