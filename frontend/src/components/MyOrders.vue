<template>
  <v-card v-if="!hasPending" class="mt-4" elevation="2" rounded="lg">
    <v-card-text class="d-flex align-center ga-2">
      <v-icon icon="mdi-check-circle" size="20" color="success" />
      <span class="text-body-2 font-weight-medium text-success">Sin pedidos pendientes</span>
    </v-card-text>
  </v-card>
  <v-card v-else class="mt-4" elevation="2" rounded="lg">
    <v-card-title class="text-subtitle-2">Mi pedido</v-card-title>
    <v-card-text>
      <v-skeleton-loader v-if="isLoading" type="list-item@2" />
      <v-card v-else-if="!displayedOrder" class="mt-2" elevation="2" rounded="lg" color="success" variant="tonal">
        <v-card-text class="d-flex align-center ga-2">
          <v-icon icon="mdi-check-circle" size="20" />
          <span class="text-body-2 font-weight-medium">Sin pedidos pendientes</span>
        </v-card-text>
      </v-card>
      <div v-else class="d-flex flex-column ga-2">
        <v-alert
          v-if="displayedOrder.state === 'ENTREGADO'"
          type="success"
          variant="tonal"
        >¡Pedido entregado! Gracias</v-alert>
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
import { useMyOrders, useCancelMyOrder, getMyOrderSnapshots, updateMyOrderSnapshotState } from '@/composables/useMyOrders'

const { data, isLoading, ids } = useMyOrders()
const cancelMut = useCancelMyOrder()
const cancellingId = ref<number | null>(null)
const errorMsg = ref<string | null>(null)

// Delivered orders show their success state for a short window so the client
// sees it, then auto-hide (same idea as cancelled orders).
const CANCELADO_AUTO_HIDE_MS = 1 * 60 * 1000
const ENTREGADO_AUTO_HIDE_MS = 5 * 60 * 1000

// Tracking is day-scoped: an order is only "mine" on the day it was placed.
// Stale ids/snapshots from previous days (e.g. an operator's shared browser)
// must never resurrect old cards like "#7 — entregado" weeks later.
function isToday(createdAt?: string | null): boolean {
  if (!createdAt) return false
  const d = new Date(createdAt)
  if (isNaN(d.getTime())) return false
  const t = new Date(now.value)
  return d.getFullYear() === t.getFullYear() && d.getMonth() === t.getMonth() && d.getDate() === t.getDate()
}

const now = ref(Date.now())
let tick: number | null = null
onMounted(() => {
  tick = window.setInterval(() => { now.value = Date.now() }, 1000)
})
onUnmounted(() => {
  if (tick !== null) window.clearInterval(tick)
})

type OrderRow = { id: number; code: number; state: string; total: string; created_at?: string | null; updated_at?: string | null }

const hasPending = computed(() => {
  // While loading, trust the tracked ids/snapshots; once loaded, only today's
  // orders keep the card alive.
  if (isLoading.value) return ids.value.length > 0 || getMyOrderSnapshots().length > 0
  const list = (data.value ?? []) as OrderRow[]
  return list.some((o) => isToday(o.created_at)) || getMyOrderSnapshots().some((s) => isToday(s.created_at))
})

const latestOrder = computed<OrderRow | null>(() => {
  const list = ((data.value ?? []) as OrderRow[]).filter((o) => isToday(o.created_at))
  if (list.length > 0) {
    const sorted = [...list].sort((a, b) => {
      const da = a.created_at ? Date.parse(a.created_at) : 0
      const db = b.created_at ? Date.parse(b.created_at) : 0
      if (db !== da) return db - da
      return b.id - a.id
    })
    const top = sorted[0] ?? null
    if (top) updateMyOrderSnapshotState(top.id, top.state)
    return top
  }
  // Fallback: la consulta falló o aún carga → usar snapshot local guardado al confirmar
  const snaps = (getMyOrderSnapshots() as OrderRow[]).filter((s) => isToday(s.created_at))
  if (snaps.length === 0) return null
  const sorted = [...snaps].sort((a, b) => {
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
  if (o.state === 'CANCELADO' || o.state === 'ENTREGADO') {
    const tsRaw = o.updated_at || o.created_at
    const ts = tsRaw ? Date.parse(tsRaw) : 0
    const hideAfterMs = o.state === 'CANCELADO' ? CANCELADO_AUTO_HIDE_MS : ENTREGADO_AUTO_HIDE_MS
    if (ts && now.value - ts > hideAfterMs) return null
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
  if (state === 'RECIBIDO') return 'warning'
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
