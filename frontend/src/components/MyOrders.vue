<template>
  <v-card v-if="ids.length === 0" class="mt-4" color="success" variant="tonal">
    <v-card-text class="d-flex align-center ga-2">
      <v-icon icon="mdi-check-circle" size="20" />
      <span class="text-body-2 font-weight-medium">Sin pedidos pendientes</span>
    </v-card-text>
  </v-card>
  <v-card v-else class="mt-4" variant="outlined">
    <v-card-title class="text-subtitle-2">Mi pedido</v-card-title>
    <v-card-text>
      <v-skeleton-loader v-if="isLoading" type="list-item@2" />
      <div v-else-if="!displayedOrder" class="d-flex align-center ga-2 text-success">
        <v-icon icon="mdi-check-circle" size="20" />
        <span class="text-body-2 font-weight-medium">Sin pedidos pendientes</span>
      </div>
      <div v-else class="d-flex flex-column ga-2">
        <v-card variant="tonal" class="pa-2" :color="cardColor(displayedOrder.state)">
          <div class="d-flex justify-space-between align-center">
            <div>
              <div class="text-body-2 font-weight-bold">#{{ displayedOrder.code }} — {{ displayedOrder.state }}</div>
              <div class="text-caption">Total: ${{ displayedOrder.total }}</div>
            </div>
            <v-chip size="x-small" :color="chipColor(displayedOrder.state)" variant="flat">{{ displayedOrder.state }}</v-chip>
          </div>
          <v-btn
            v-if="displayedOrder.state === 'RECIBIDO'"
            size="small"
            color="error"
            variant="tonal"
            class="mt-2"
            block
            :loading="cancellingId === displayedOrder.id"
            @click="cancel(displayedOrder.id)"
            >Anular pedido</v-btn
          >
        </v-card>
      </div>
      <div v-if="errorMsg" class="text-caption text-error mt-2">{{ errorMsg }}</div>
    </v-card-text>
  </v-card>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useMyOrders, useCancelMyOrder } from '@/composables/useMyOrders'

const { data, isLoading, ids } = useMyOrders()
const cancelMut = useCancelMyOrder()
const cancellingId = ref<number | null>(null)
const errorMsg = ref<string | null>(null)

const ENTREGADO_AUTO_HIDE_MS = 1 * 60 * 1000

const now = ref(Date.now())
let tick: number | null = null
onMounted(() => {
  tick = window.setInterval(() => { now.value = Date.now() }, 1000)
})
onUnmounted(() => {
  if (tick !== null) window.clearInterval(tick)
})

type OrderRow = { id: number; code: number; state: string; total: string; created_at?: string | null; updated_at?: string | null }

const latestOrder = computed<OrderRow | null>(() => {
  const list = (data.value ?? []) as OrderRow[]
  if (list.length === 0) return null
  const sorted = [...list].sort((a, b) => {
    const da = a.created_at ? Date.parse(a.created_at) : 0
    const db = b.created_at ? Date.parse(b.created_at) : 0
    if (db !== da) return db - da
    return b.id - a.id
  })
  return sorted[0] ?? null
})

const displayedOrder = computed<OrderRow | null>(() => {
  const o = latestOrder.value
  if (!o) return null
  if (o.state === 'ENTREGADO') {
    const tsRaw = o.updated_at || o.created_at
    const ts = tsRaw ? Date.parse(tsRaw) : 0
    if (ts && now.value - ts > ENTREGADO_AUTO_HIDE_MS) return null
  }
  return o
})

const STATE_CHIP_COLOR: Record<string, string> = {
  RECIBIDO: 'warning',
  PREPARACION: 'deep-orange',
  FACTURACION: 'primary',
  LOGISTICA: 'purple',
  ENTREGADO: 'success',
  CANCELADO: 'error',
}

function chipColor(state: string): string {
  return STATE_CHIP_COLOR[state] ?? 'default'
}

function cardColor(state: string): string {
  if (state === 'RECIBIDO') return 'success'
  if (state === 'ENTREGADO') return 'success'
  return chipColor(state)
}

async function cancel(id: number) {
  errorMsg.value = null
  const target = (data.value ?? []).find((o: { id: number; state: string }) => o.id === id) as { state: string } | undefined
  if (target && target.state !== 'RECIBIDO') {
    errorMsg.value = 'Solo se puede anular en RECIBIDO'
    return
  }
  cancellingId.value = id
  try {
    await cancelMut.mutateAsync(id)
  } catch (e: unknown) {
    const response = (e as { response?: { data?: { error?: { message?: string } } } })?.response
    errorMsg.value = response?.data?.error?.message || 'No se pudo anular el pedido'
  } finally {
    cancellingId.value = null
  }
}
</script>
