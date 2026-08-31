<template>
  <v-container fluid>
    <div class="d-flex justify-space-between align-center mb-4">
      <h2>Kanban — Ice Zone</h2>
      <v-text-field v-model="businessDate" type="date" density="compact" hide-details style="max-width: 180px" />
    </div>
    <v-alert v-if="alreadyClosed" type="info" class="mb-4">Caja del {{ formatDM(today) }} cerrada — pedidos nuevos irán al {{ formatDM(tomorrow) }}. Pedidos del día archivados.</v-alert>
    <WeatherForecast />
    <v-row>
      <v-col v-for="col in cols" :key="col.state" cols="12" md="2">
        <KanbanColumn :title="col.title" :color="col.color" :orders="getOrdersFor(col.state)" :is-loading="getLoadingFor(col.state)" :is-error="getErrorFor(col.state)" :compact="col.state === 'ENTREGADO'" @retry="boards[col.state].refetch()" />
      </v-col>
      <v-col cols="12" md="2">
        <KanbanTotalsCard :fallback-orders="(boards['ENTREGADO'].data.value ?? []) as any" :business-date="businessDate" />
      </v-col>
    </v-row>
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
const cols = [
  { state: 'RECIBIDO', title: 'Recibido', color: COLUMN_COLORS.RECIBIDO },
  { state: 'PREPARACION', title: 'Preparación', color: COLUMN_COLORS.PREPARACION },
  { state: 'FACTURACION', title: 'Facturación', color: COLUMN_COLORS.FACTURACION },
  { state: 'LOGISTICA', title: 'Logística', color: COLUMN_COLORS.LOGISTICA },
  { state: 'ENTREGADO', title: 'Entregado', color: COLUMN_COLORS.ENTREGADO },
] as const
const boards: Record<string, ReturnType<typeof useOrdersBoard>> = {}
for (const c of cols) boards[c.state] = useOrdersBoard(c.state, businessDate)
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
