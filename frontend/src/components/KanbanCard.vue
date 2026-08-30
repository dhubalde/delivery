<template>
  <v-tooltip v-if="compact" location="top" open-on-hover>
    <template #activator="{ props: tipProps }">
      <v-card v-bind="tipProps" :loading="pending" class="mb-1" density="compact" height="60">
        <v-card-text class="py-1 px-2 d-flex flex-column justify-center" style="height: 60px; min-width: 0">
          <div class="d-flex align-center text-caption font-weight-bold" style="min-width: 0; font-size: 12px; line-height: 1.2">
            <span class="flex-shrink-0">#{{ order.code }} —&nbsp;</span>
            <span class="text-truncate flex-1">{{ order.customer_name ?? order.customer ?? '—' }}</span>
          </div>
          <div class="text-caption text-medium-emphasis text-truncate" style="font-size: 11px; line-height: 1.2; white-space: nowrap">
            <span v-if="hour">{{ hour }} · </span>${{ order.total }}
          </div>
        </v-card-text>
      </v-card>
    </template>
    <div class="pa-1" style="min-width: 180px">
      <div class="font-weight-bold">#{{ order.code }}</div>
      <div>{{ order.customer_name ?? order.customer ?? '—' }}</div>
      <div>Total ${{ order.total }}</div>
      <div v-if="hour">Hora {{ hour }}</div>
      <div v-if="orderAddress">{{ orderAddress }}</div>
      <div v-if="orderPhone">{{ orderPhone }}</div>
    </div>
  </v-tooltip>
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

const props = defineProps<{ order: { id: number; code: string; state: string; fulfillment: string; cash_declared: boolean; total: string; payments: { method: string; status: string }[]; customer_name?: string; customer?: string; created_at?: string; address?: string; phone?: string; customer_address?: string; customer_phone?: string; delivery_address?: string }; compact?: boolean }>()
const orderAddress = computed(() => (props.order as unknown as Record<string, string | undefined>).address ?? (props.order as unknown as Record<string, string | undefined>).customer_address ?? (props.order as unknown as Record<string, string | undefined>).delivery_address ?? '')
const orderPhone = computed(() => (props.order as unknown as Record<string, string | undefined>).phone ?? (props.order as unknown as Record<string, string | undefined>).customer_phone ?? '')
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
    const response = (e as { response?: { status?: number; data?: { error?: { code?: string; message?: string } } } })?.response
    const status = response?.status
    const serverMsg = response?.data?.error?.message
    if (status === 409) {
      const msg = serverMsg || 'Estado ya cambió'
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg, type: 'warning' } }))
      console.warn(`[409] ${msg}`)
    } else if (status === 403) {
      const msg = serverMsg || 'Permiso denegado'
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg, type: 'error' } }))
      console.warn('[403] Permiso denegado')
    } else if (status && status >= 500) {
      const msg = serverMsg || 'Error de servidor'
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg, type: 'error' } }))
      console.error(`[${status}] ${msg}`)
    } else if (serverMsg) {
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg: serverMsg, type: 'error' } }))
    }
  }
}
</script>
<style scoped>
.blinking { animation: blink 1s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
</style>
