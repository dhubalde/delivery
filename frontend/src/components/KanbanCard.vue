<template>
  <v-card v-if="compact" :loading="pending" class="mb-1" density="compact" height="60">
    <v-card-text class="py-1 px-2 d-flex align-center justify-space-between text-caption" style="height: 60px">
      <span class="text-truncate"><strong>#{{ order.code }}</strong> · {{ order.customer_name ?? order.customer ?? '—' }}</span>
      <span class="d-flex align-center ga-2 flex-shrink-0 ml-2"><strong>${{ order.total }}</strong><span v-if="hour" class="text-medium-emphasis">{{ hour }}</span></span>
    </v-card-text>
  </v-card>
  <v-card v-else :loading="pending" class="mb-2" density="compact">
    <v-card-text class="pb-1">
      <div class="d-flex justify-space-between align-center">
        <strong>#{{ order.code }}</strong>
        <v-chip v-if="hasPending" size="x-small" color="warning" class="blinking">PENDING</v-chip>
      </div>
      <div class="text-caption">{{ order.customer_name ?? order.customer ?? '—' }} · {{ order.fulfillment }}</div>
      <div class="text-caption font-weight-bold">${{ order.total }}</div>
    </v-card-text>
    <v-card-actions v-if="!isTerminal">
      <v-tooltip :text="tooltip">
        <template #activator="{ props }">
          <span v-bind="props" class="w-100">
            <v-btn :disabled="!canAdvanceOk || pending" block size="small" color="primary" @click="onAdvance">Avanzar</v-btn>
          </span>
        </template>
      </v-tooltip>
    </v-card-actions>
  </v-card>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth.store'
import { canAdvance, nextStateOf } from '@/utils/guards'
import { useTransition } from '@/composables/useOrders'

const props = defineProps<{ order: { id: number; code: string; state: string; fulfillment: string; cash_declared: boolean; total: string; payments: { method: string; status: string }[]; customer_name?: string; customer?: string; created_at?: string }; compact?: boolean }>()
const auth = useAuthStore()
const tr = useTransition()
const hour = computed(() => {
  const raw = props.order.created_at
  if (!raw) return ''
  try { return new Date(raw).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }) } catch { return '' }
})
const isTerminal = computed(() => ['ENTREGADO', 'CANCELADO'].includes(props.order.state))
const hasPending = computed(() => props.order.payments?.some((p) => p.status === 'PENDING'))
const guard = computed(() => canAdvance(props.order.state, auth.roles, props.order))
const canAdvanceOk = computed(() => guard.value.ok)
const tooltip = computed(() => (guard.value.ok ? `Avanzar a ${nextStateOf(props.order.state)}` : guard.value.reason))
const pending = computed(() => tr.isPending.value)
async function onAdvance() {
  const to = nextStateOf(props.order.state)
  if (!to || !guard.value.ok) return
  try {
    await tr.mutateAsync({ id: props.order.id, to_state: to })
  } catch (e: unknown) {
    const status = (e as { response?: { status?: number } })?.response?.status
    if (status === 409) console.warn('[409] Estado ya cambió')
    if (status === 403) console.warn('[403] Permiso denegado')
  }
}
</script>
<style scoped>
.blinking { animation: blink 1s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
</style>
