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
const today = new Date().toISOString().slice(0, 10)
const tomorrow = (() => {
  const d = new Date(today)
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
})()
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
