<template>
  <v-card v-if="ids.length > 0" class="mt-4" variant="outlined">
    <v-card-title class="text-subtitle-2">Mis pedidos</v-card-title>
    <v-card-text>
      <v-skeleton-loader v-if="isLoading" type="list-item@2" />
      <div v-else-if="visibleOrders.length === 0" class="text-caption text-medium-emphasis">
        Sin pedidos pendientes en RECIBIDO
      </div>
      <div v-else class="d-flex flex-column ga-2">
        <v-card v-for="order in visibleOrders" :key="order.id" variant="tonal" class="pa-2" color="warning">
          <div class="d-flex justify-space-between align-center">
            <div>
              <div class="text-body-2 font-weight-bold">#{{ order.code }} — {{ order.state }}</div>
              <div class="text-caption">Total: ${{ order.total }}</div>
            </div>
            <v-chip size="x-small" color="warning">{{ order.state }}</v-chip>
          </div>
          <v-btn size="small" color="error" variant="tonal" class="mt-2" block :loading="cancellingId === order.id" @click="cancel(order.id)">Anular pedido</v-btn>
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

const visibleOrders = computed(() => {
  const list = (data.value ?? []) as { id: number; code: number; state: string; total: string }[]
  return list.filter((o) => o.state === 'RECIBIDO')
})

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
