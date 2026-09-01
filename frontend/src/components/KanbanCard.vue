<template>
  <v-tooltip v-if="effectiveCompact" location="top" open-on-hover>
    <template #activator="{ props: tipProps }">
      <v-card v-bind="tipProps" :loading="pending" class="mb-1" density="compact" height="60" :color="isRejected ? 'error' : undefined" :variant="isRejected ? 'outlined' : 'elevated'" :style="isRejected ? 'border:2px solid rgb(var(--v-theme-error))' : undefined">
        <v-card-text class="py-1 px-2 d-flex flex-column justify-center" style="height: 60px; min-width: 0" :class="{ 'text-error': isRejected }">
          <div class="d-flex align-center text-caption font-weight-bold" style="min-width: 0; font-size: 12px; line-height: 1.2" :class="{ 'text-error': isRejected }">
            <span class="flex-shrink-0">#{{ order.code }} —&nbsp;</span>
            <span class="text-truncate flex-1">{{ order.customer_name ?? order.customer ?? '—' }}</span>
          </div>
          <div class="text-caption text-truncate" :class="isRejected ? 'text-error' : 'text-medium-emphasis'" style="font-size: 11px; line-height: 1.2; white-space: nowrap">
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
  <v-card v-else :loading="pending" class="mb-2" density="compact" :color="isRejected ? 'error' : undefined" :variant="isRejected ? 'outlined' : 'elevated'" :style="isRejected ? 'border:2px solid rgb(var(--v-theme-error))' : undefined" :class="{ 'rejected-card': isRejected }">
    <v-card-text class="pb-1" :class="{ 'text-error': isRejected }">
      <div class="d-flex justify-space-between align-center">
        <strong :class="{ 'text-error': isRejected }">#{{ order.code }}</strong>
        <v-chip v-if="isRejected" size="x-small" color="error">No entregado</v-chip>
        <v-chip v-else-if="hasPending" size="x-small" color="warning" class="blinking">PENDING</v-chip>
      </div>
      <div class="text-caption" :class="isRejected ? 'text-error' : ''">{{ order.customer_name ?? order.customer ?? '—' }} · {{ order.fulfillment }}</div>
      <div class="text-caption font-weight-bold" :class="{ 'text-error': isRejected }">${{ order.total }}</div>
      <div v-if="isRejected && (order as any).cancel_reason" class="text-caption text-error mt-1" style="white-space: normal; line-height: 1.2">{{ (order as any).cancel_reason }}</div>
    </v-card-text>
    <v-card-actions v-if="isRejected" class="d-flex flex-column ga-1">
      <v-tooltip text="Próximamente">
        <template #activator="{ props: tipProps }">
          <span v-bind="tipProps" class="w-100">
            <v-btn block size="small" variant="outlined" disabled>Revertir</v-btn>
          </span>
        </template>
      </v-tooltip>
    </v-card-actions>
    <v-card-actions v-else-if="!isTerminal" :class="isLogistica ? 'd-flex flex-column ga-1' : 'd-flex ga-2'">
      <v-tooltip :text="tooltip">
        <template #activator="{ props }">
          <span v-bind="props" :class="isLogistica ? 'w-100' : 'flex-1'">
            <v-btn :disabled="!canAdvanceOk || pending" block size="small" color="primary" @click="onAdvance">Avanzar</v-btn>
          </span>
        </template>
      </v-tooltip>
      <v-btn v-if="isLogistica" :disabled="pending" size="x-small" color="error" variant="text" block density="compact" style="font-size:11px;border:none" @click="openReject">NO ENTREGADO</v-btn>
    </v-card-actions>
  </v-card>

  <v-dialog v-model="rejectDialog" max-width="480" persistent>
    <v-card>
      <v-card-title class="text-subtitle-1">Motivo de no entrega — #{{ order.code }}</v-card-title>
      <v-card-text class="d-flex flex-column ga-3">
        <v-select v-model="rejectMotivo" :items="motivoOptions" label="Motivo *" :error="showMotivoError" :error-messages="showMotivoError ? 'Seleccioná un motivo' : ''" density="compact" variant="outlined" hide-details="auto" />
        <v-textarea v-model="rejectDetalle" label="Detalle (opcional)" rows="2" auto-grow density="compact" variant="outlined" hide-details placeholder="Ej: cliente no atendió timbre, dirección inexistente..." />
        <div v-if="rejectMotivo === 'Otro' && !hasDetalle" class="text-caption text-error">Si elegís "Otro" detallá el motivo</div>
      </v-card-text>
      <v-card-actions class="justify-end ga-2">
        <v-btn variant="text" :disabled="pending" @click="rejectDialog = false">Cancelar</v-btn>
        <v-btn color="error" :disabled="!canConfirmReject || pending" :loading="pending" @click="onConfirmReject">Confirmar rechazo</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAuthStore } from '@/stores/auth.store'
import { canAdvance, hasAnyRole, nextStateOf, requiredRolesFor } from '@/utils/guards'
import { useTransition } from '@/composables/useOrders'

const props = defineProps<{ order: { id: number; code: string; state: string; fulfillment: string; cash_declared: boolean; total: string; payments: { method: string; status: string }[]; customer_name?: string; customer?: string; created_at?: string; address?: string; phone?: string; customer_address?: string; customer_phone?: string; delivery_address?: string; cancel_reason?: string | null; canceled_at?: string | null }; compact?: boolean }>()
const orderAddress = computed(() => (props.order as unknown as Record<string, string | undefined>).address ?? (props.order as unknown as Record<string, string | undefined>).customer_address ?? (props.order as unknown as Record<string, string | undefined>).delivery_address ?? '')
const orderPhone = computed(() => (props.order as unknown as Record<string, string | undefined>).phone ?? (props.order as unknown as Record<string, string | undefined>).customer_phone ?? '')
const auth = useAuthStore()
const tr = useTransition()
const hour = computed(() => {
  const raw = props.order.created_at
  if (!raw) return ''
  try { return new Date(raw).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }) } catch { return '' }
})
const isRejected = computed(() => props.order.state === 'CANCELADO' || !!(props.order as unknown as { cancel_reason?: string | null }).cancel_reason)
const effectiveCompact = computed(() => !!props.compact || (isRejected.value && (props.order.state === 'LOGISTICA' || props.order.state === 'CANCELADO')))
const isTerminal = computed(() => ['ENTREGADO', 'CANCELADO'].includes(props.order.state))
const isLogistica = computed(() => props.order.state === 'LOGISTICA')
const hasPending = computed(() => props.order.payments?.some((p) => p.status === 'PENDING'))
const guard = computed(() => canAdvance(props.order.state, auth.roles, props.order))
const canAdvanceOk = computed(() => guard.value.ok)
const tooltip = computed(() => (guard.value.ok ? `Avanzar a ${nextStateOf(props.order.state)}` : guard.value.reason))
const pending = computed(() => tr.isPending.value)
const rejectDialog = ref(false)
const rejectMotivo = ref('')
const rejectDetalle = ref('')
const attempted = ref(false)
const motivoOptions = ['Cliente no atendió', 'Dirección incorrecta', 'Broma', 'Cliente rechazó', 'Otro']
const hasDetalle = computed(() => rejectDetalle.value.trim().length > 0)
const showMotivoError = computed(() => attempted.value && !rejectMotivo.value)
const canConfirmReject = computed(() => {
  if (!rejectMotivo.value) return false
  if (rejectMotivo.value === 'Otro' && !hasDetalle.value) return false
  const roles = requiredRolesFor('LOGISTICA', 'CANCELADO')
  if (roles.length && !hasAnyRole(auth.roles, roles)) return false
  return true
})
function openReject() {
  rejectMotivo.value = ''
  rejectDetalle.value = ''
  attempted.value = false
  rejectDialog.value = true
}
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
async function onConfirmReject() {
  attempted.value = true
  if (!canConfirmReject.value) return
  const reason = rejectMotivo.value === 'Otro' ? `Otro: ${rejectDetalle.value.trim()}` : (hasDetalle.value ? `${rejectMotivo.value} - ${rejectDetalle.value.trim()}` : rejectMotivo.value)
  try {
    await tr.mutateAsync({ id: props.order.id, to_state: 'CANCELADO', reason })
    rejectDialog.value = false
  } catch (e: unknown) {
    const response = (e as { response?: { status?: number; data?: { error?: { code?: string; message?: string } } } })?.response
    const status = response?.status
    const serverMsg = response?.data?.error?.message
    if (status === 400 && serverMsg) {
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg: serverMsg, type: 'error' } }))
    } else if (status === 409) {
      const msg = serverMsg || 'Estado ya cambió'
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg, type: 'warning' } }))
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
