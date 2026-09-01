<template>
  <v-container>
    <div class="d-flex justify-space-between align-center mb-4 flex-wrap ga-4">
      <h2 style="font-family: Comfortaa">Dashboard — Reportes</h2>
      <v-text-field v-model="businessDate" type="date" density="compact" hide-details style="max-width: 180px" label="Fecha" />
    </div>
    <v-skeleton-loader v-if="cashLoading || ordersLoading" type="card" />
    <v-alert v-else-if="cashError" type="warning" class="mb-4">Sin datos para {{ businessDate }} — mostrando cálculo local</v-alert>
    <v-row class="mb-4">
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-caption text-medium-emphasis">Total pedidos</div>
            <div class="text-h5 font-weight-bold">{{ totalPedidos }}</div>
            <div class="text-caption">Entregados {{ entregados }} + Rechazados {{ rechazados }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-caption text-medium-emphasis">Total ventas</div>
            <div class="text-h5 font-weight-bold">${{ fmt(totalVentas) }}</div>
            <div class="text-caption">EF ${{ fmt(efectivo) }} · BV ${{ fmt(billeteras) }} · TJ ${{ fmt(tarjetas) }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-caption text-medium-emphasis">Ticket promedio</div>
            <div class="text-h5 font-weight-bold">${{ fmt(ticketPromedio) }}</div>
            <div class="text-caption">sobre {{ entregados }} entregados</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-caption text-medium-emphasis">Rechazados</div>
            <div class="text-h5 font-weight-bold">{{ rechazados }}</div>
            <div class="text-caption">{{ rechazadosPct }}% del total</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-card v-if="hasBoardData" class="mb-4">
      <v-card-title class="text-subtitle-2">Detalle por board ({{ businessDate }})</v-card-title>
      <v-card-text class="d-flex ga-4 flex-wrap">
        <span>ENTREGADO board: {{ boardEntregados.length }}</span>
        <span>CANCELADO board: {{ boardCancelados.length }}</span>
      </v-card-text>
    </v-card>
  </v-container>
</template>
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useCashPreview } from '@/composables/useCashClose'
import { useOrdersBoard } from '@/composables/useOrders'

function getBusinessDateStr(d = new Date()): string {
  return d.toLocaleDateString('en-CA', { timeZone: 'America/Argentina/Buenos_Aires' })
}

const businessDate = ref(getBusinessDateStr())
const businessDateRef = computed(() => businessDate.value)

const { data: cashData, isLoading: cashLoading, isError: cashError } = useCashPreview(businessDateRef)

type CashTotals = { EFECTIVO: string; BILLETERAS_VIRTUALES: string; TARJETAS: string; TOTAL_ENTREGADOS: number; TOTAL_RECHAZADOS: number }
const totals = computed<CashTotals>(() => {
  const t = (cashData.value as { totals?: CashTotals } | undefined)?.totals
  return t ?? { EFECTIVO: '0.00', BILLETERAS_VIRTUALES: '0.00', TARJETAS: '0.00', TOTAL_ENTREGADOS: 0, TOTAL_RECHAZADOS: 0 }
})

const efectivo = computed(() => Number.parseFloat(String(totals.value.EFECTIVO ?? 0)) || 0)
const billeteras = computed(() => Number.parseFloat(String(totals.value.BILLETERAS_VIRTUALES ?? 0)) || 0)
const tarjetas = computed(() => Number.parseFloat(String(totals.value.TARJETAS ?? 0)) || 0)
const totalVentas = computed(() => efectivo.value + billeteras.value + tarjetas.value)
const entregados = computed(() => Number(totals.value.TOTAL_ENTREGADOS ?? 0))
const rechazados = computed(() => Number(totals.value.TOTAL_RECHAZADOS ?? 0))
const totalPedidos = computed(() => entregados.value + rechazados.value)
const ticketPromedio = computed(() => (entregados.value > 0 ? totalVentas.value / entregados.value : 0))
const rechazadosPct = computed(() => (totalPedidos.value > 0 ? ((rechazados.value / totalPedidos.value) * 100).toFixed(1) : '0.0'))

const entregadoBoard = useOrdersBoard('ENTREGADO', businessDateRef)
const canceladoBoard = useOrdersBoard('CANCELADO', businessDateRef)
const boardEntregados = computed(() => (entregadoBoard.data.value ?? []) as unknown[])
const boardCancelados = computed(() => (canceladoBoard.data.value ?? []) as unknown[])
const hasBoardData = computed(() => boardEntregados.value.length > 0 || boardCancelados.value.length > 0)
const ordersLoading = computed(() => entregadoBoard.isLoading.value || canceladoBoard.isLoading.value)

function fmt(n: number) {
  return n.toFixed(2)
}
</script>
