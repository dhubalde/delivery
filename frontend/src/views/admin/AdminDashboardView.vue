<template>
  <v-container>
    <div class="d-flex justify-space-between align-center mb-4 flex-wrap ga-4">
      <h2 style="font-family: Comfortaa">Dashboard — Reportes</h2>
      <div class="d-flex align-center ga-2">
        <v-text-field v-model="startDate" type="date" density="compact" hide-details label="Desde" style="max-width: 200px" menu />
        <v-text-field v-model="endDate" type="date" density="compact" hide-details label="Hasta" style="max-width: 200px" menu />
      </div>
    </div>
    <v-skeleton-loader v-if="cashLoading || ordersLoading" type="card" />
    <v-alert v-else-if="cashError" type="warning" class="mb-4">Sin datos para {{ startDate }} — mostrando cálculo local</v-alert>
    <v-row class="mb-4" align="stretch">
      <v-col cols="12" sm="6" md="3">
        <v-card class="flex-grow-1 d-flex flex-column" height="100%">
          <v-card-text class="flex-grow-1">
            <div class="text-caption text-medium-emphasis">Total pedidos</div>
            <div class="text-h5 font-weight-bold" style="color: #06B6D4">{{ totalPedidos }}</div>
            <div class="text-caption">Entregados {{ entregados }} + Rechazados {{ rechazados }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="flex-grow-1 d-flex flex-column" height="100%">
          <v-card-text class="flex-grow-1">
            <div class="text-caption text-medium-emphasis">Total ventas</div>
            <div class="text-h5 font-weight-bold" style="color: #06B6D4">${{ fmt(totalVentas) }}</div>
            <div class="text-caption">
                <div>EF ${{ fmt(efectivo) }}</div>
                <div>BV ${{ fmt(billeteras) }}</div>
                <div>TJ ${{ fmt(tarjetas) }}</div>
              </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
<v-card class="flex-grow-1 d-flex flex-column" height="100%">
          <v-card-text class="flex-grow-1">
            <div class="text-caption text-medium-emphasis">Ticket promedio</div>
            <div class="text-h5 font-weight-bold" style="color: #06B6D4">{{ fmt(ticketPromedio) }}</div>
            <div class="text-caption">sobre {{ entregados }} entregados</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="flex-grow-1 d-flex flex-column" height="100%">
          <v-card-text class="flex-grow-1">
            <div class="text-caption text-medium-emphasis">Rechazados</div>
            <div class="text-h5 font-weight-bold" style="color: #06B6D4">{{ rechazados }}</div>
            <div class="text-caption">{{ rechazadosPct }}% del total</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row class="mb-4" align="stretch">
      <v-col cols="12" md="3">
        <v-card class="flex-grow-1 d-flex flex-column" height="100%">
          <v-card-text class="flex-grow-1">
            <div class="text-caption text-medium-emphasis">Visitantes / Compradores</div>
            <div class="d-flex align-center ga-4">
              <span>
                <span class="text-h5 font-weight-bold">{{ visitCount }}</span>
                <span class="text-caption text-medium-emphasis"> entraron</span>
              </span>
              <span>
                <span class="text-h5 font-weight-bold text-primary">{{ buyerCount }}</span>
                <span class="text-caption text-medium-emphasis"> compraron</span>
              </span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-card v-if="hasBoardData" class="mb-4">
      <v-card-title class="text-subtitle-2">Detalle por board ({{ startDate }})</v-card-title>
      <v-card-text class="d-flex ga-4 flex-wrap">
        <span>ENTREGADO board: {{ boardEntregados.length }}</span>
        <span>CANCELADO board: {{ boardCancelados.length }}</span>
      </v-card-text>
    </v-card>
  </v-container>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useCashPreview } from '@/composables/useCashClose'
import { useOrdersBoard } from '@/composables/useOrders'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth.store'

function getBusinessDateStr(d = new Date()): string {
  const date = new Date(d.toLocaleString('en-US', { timeZone: 'America/Argentina/Buenos_Aires' }))
  return date.toISOString().slice(0, 10)
}

const auth = useAuthStore()
const startDate = ref(getBusinessDateStr())
const endDate = ref(getBusinessDateStr())
const businessDateRef = computed(() => startDate.value)
const endDateRef = computed(() => endDate.value)
const visitCount = ref(0)
const buyerCount = ref(0)

onMounted(async () => {
  try {
    const { data } = await api.get(`/public/${auth.merchantSlug ?? 'ice-zone'}/stat/`)
    visitCount.value = data?.visit_count ?? 0
    buyerCount.value = data?.buyer_count ?? 0
  } catch (err) {
    console.error('Failed to load catalog stats', err)
  }
})

const { data: cashData, isLoading: cashLoading, isError: cashError } = useCashPreview(businessDateRef, endDateRef)

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

const entregadoBoard = useOrdersBoard('ENTREGADO', businessDateRef, endDateRef)
const canceladoBoard = useOrdersBoard('CANCELADO', businessDateRef, endDateRef)
const boardEntregados = computed(() => (entregadoBoard.data.value ?? []) as unknown[])
const boardCancelados = computed(() => (canceladoBoard.data.value ?? []) as unknown[])
const hasBoardData = computed(() => boardEntregados.value.length > 0 || boardCancelados.value.length > 0)
const ordersLoading = computed(() => entregadoBoard.isLoading.value || canceladoBoard.isLoading.value)

function fmt(n: number) {
  return n.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>