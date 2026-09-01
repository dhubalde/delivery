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
      <div v-else-if="!currentOrder" class="d-flex align-center ga-2 text-success">
        <v-icon icon="mdi-check-circle" size="20" />
        <span class="text-body-2 font-weight-medium">Sin pedidos pendientes</span>
      </div>
      <div v-else class="d-flex flex-column ga-2">
        <v-card variant="tonal" class="pa-2" :color="cardColor(currentOrder.state)">
          <div class="d-flex justify-space-between align-center">
            <div>
              <div class="text-body-2 font-weight-bold">#{{ currentOrder.code }} — {{ currentOrder.state }}</div>
              <div class="text-caption">Total: ${{ currentOrder.total }}</div>
            </div>
            <v-chip size="x-small" :color="chipColor(currentOrder.state)" variant="flat">{{ currentOrder.state }}</v-chip>
          </div>
          <v-btn
            v-if="currentOrder.state === 'RECIBIDO'"
            size="small"
            color="error"
            variant="tonal"
            class="mt-2"
            block
            :loading="cancellingId === currentOrder.id"
            @click="cancel(currentOrder.id)"
            >Anular pedido</v-btn
          >
        </v-card>
      </div>
      <div v-if="errorMsg" class="text-caption text-error mt-2">{{ errorMsg }}</div>
    </v-card-text>
  </v-card>
</template>
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMyOrders, useCancelMyOrder } from '@/composables/useMyOrders'

const { data, isLoading, ids } = useMyOrders()
const cancelMut = useCancelMyOrder()
const cancellingId = ref<number | null>(null)
const errorMsg = ref<string | null>(null)

const ACTIVE_STATES = ['RECIBIDO', 'PREPARACION', 'FACTURACION', 'LOGISTICA'] as const

const currentOrder = computed(() => {
  const list = (data.value ?? []) as { id: number; code: number; state: string; total: string }[]
  if (list.length === 0) return null
  const active = list.filter((o) => (ACTIVE_STATES as readonly string[]).includes(o.state))
  if (active.length > 0) return active.reduce((a, b) => (a.id > b.id ? a : b))
  return list.reduce((a, b) => (a.id > b.id ? a : b))
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
