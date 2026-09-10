<template>
  <v-container fluid class="ma-0 pa-2" style="margin:0;padding:8px;box-sizing:border-box;max-width:100%;width:100%">
    <div class="d-flex justify-space-between align-center mb-4 w-100 ma-0 pa-0" style="margin:0;padding:0;box-sizing:border-box;width:100%">
      <h2>Kanban — {{ merchantName }}</h2>
      <v-text-field v-model="businessDate" type="date" density="compact" hide-details style="max-width: 180px" />
    </div>
    <v-alert v-if="alreadyClosed" type="info" class="mb-4 ma-0" style="margin:0 0 16px 0;box-sizing:border-box;width:100%">Caja del {{ formatDM(today) }} cerrada — pedidos nuevos irán al {{ formatDM(tomorrow) }}. Pedidos del día archivados.</v-alert>
    <WeatherForecast />
    <!-- CSS grid is cross-browser consistent; avoids flex-basis:0 vs md="2" (16.66% max-width) divergence that made Edge narrow -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;width:100%;margin:0;padding:0;box-sizing:border-box">
      <div v-for="col in cols" :key="col.state" style="min-width:0;display:flex;box-sizing:border-box;width:100%">
        <KanbanColumn :title="col.title" :color="col.color" :orders="getOrdersFor(col.state)" :is-loading="getLoadingFor(col.state)" :is-error="getErrorFor(col.state)" :compact="col.state === 'ENTREGADO'" @retry="boards[col.state].refetch()" />
      </div>
      <div style="min-width:0;display:flex;box-sizing:border-box;width:100%">
        <KanbanTotalsCard :fallback-orders="(boards['ENTREGADO'].data.value ?? []) as any" :business-date="businessDate" />
      </div>
    </div>
  </v-container>
</template>
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { COLUMN_COLORS } from '@/theme/tokens'
import { useOrdersBoard } from '@/composables/useOrders'
import { useCashPreview } from '@/composables/useCashClose'
import KanbanColumn from '@/components/KanbanColumn.vue'
import KanbanTotalsCard from '@/components/KanbanTotalsCard.vue'
import WeatherForecast from '@/components/WeatherForecast.vue'
import { useMerchant } from '@/composables/useMerchant'
import { useAuthStore } from '@/stores/auth.store'
const { data: merchantData } = useMerchant()
const merchantName = computed(() => (merchantData.value as { name?: string } | undefined)?.name ?? 'Work Zone')
const auth = useAuthStore()
const stationSector = computed(() => {
  const u = auth.user as { kind?: string; sector?: string | null; role?: string } | null
  if (!u || u.role === 'ADMIN' || u.role === 'MASTER') return null
  if (u.sector && u.sector !== 'TODAS') return u.sector
  return null
})
function getBusinessDateStr(d = new Date()): string {
  const dateStr = d.toLocaleDateString('en-CA', { timeZone: 'America/Argentina/Buenos_Aires' })
  const hourStr = d.toLocaleString('en-GB', { timeZone: 'America/Argentina/Buenos_Aires', hour: '2-digit', hour12: false })
  const hour = Number.parseInt(hourStr, 10)
  if (Number.isNaN(hour)) return dateStr
  if (hour < 3) {
    const tmp = new Date(`${dateStr}T12:00:00`)
    tmp.setDate(tmp.getDate() - 1)
    return tmp.toISOString().slice(0, 10)
  }
  return dateStr
}
function addDays(iso: string, days: number): string {
  const d = new Date(`${iso}T12:00:00`)
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}
const today = getBusinessDateStr()
const tomorrow = addDays(today, 1)
const businessDate = ref(today)
const { data: cashData } = useCashPreview(businessDate)
const alreadyClosed = computed(() => !!(cashData.value as { already_closed?: boolean } | undefined)?.already_closed)
const isTodayClosed = computed(() => alreadyClosed.value && businessDate.value === today)
const formatDM = (iso: string) => {
  const [, m, d] = iso.split('-')
  return `${d}/${m}`
}
watch(
  () => alreadyClosed.value,
  (v) => {
    if (v && businessDate.value === today) businessDate.value = tomorrow
  },
  { immediate: true },
)
const allCols = [
  { state: 'RECIBIDO', title: 'Recibido', color: COLUMN_COLORS.RECIBIDO },
  { state: 'PREPARACION', title: 'Preparación', color: COLUMN_COLORS.PREPARACION },
  { state: 'FACTURACION', title: 'Facturación', color: COLUMN_COLORS.FACTURACION },
  { state: 'LOGISTICA', title: 'Logística', color: COLUMN_COLORS.LOGISTICA },
  { state: 'ENTREGADO', title: 'Entregado', color: COLUMN_COLORS.ENTREGADO },
] as const
const cols = computed(() =>
  stationSector.value ? allCols.filter((c) => c.state === stationSector.value) : [...allCols],
)
const boards: Record<string, ReturnType<typeof useOrdersBoard>> = {}
for (const c of allCols) boards[c.state] = useOrdersBoard(c.state, businessDate)
const canceladoBoard = useOrdersBoard('CANCELADO', businessDate)
function getOrdersFor(state: string) {
  if (state === 'LOGISTICA') {
    const base = (boards['LOGISTICA'].data.value ?? []) as unknown as { cancel_reason?: string | null }[]
    const rejected = ((canceladoBoard.data.value ?? []) as unknown as { cancel_reason?: string | null }[]).filter((o) => !!o.cancel_reason)
    return [...(base as never[]), ...(rejected as never[])] as never[]
  }
  return (boards[state].data.value ?? []) as never[]
}
function getLoadingFor(state: string) {
  if (state === 'LOGISTICA') return boards['LOGISTICA'].isLoading.value || canceladoBoard.isLoading.value
  return boards[state].isLoading.value
}
function getErrorFor(state: string) {
  if (state === 'LOGISTICA') return boards['LOGISTICA'].isError.value || canceladoBoard.isError.value
  return boards[state].isError.value
}
</script>
