<template>
  <v-container>
    <h2 style="font-family:Comfortaa" class="mb-4">Cierre de caja</h2>
    <v-alert v-if="!isAdmin" type="warning" class="mb-4">Solo ADMIN puede cerrar caja (BR-CIE-01)</v-alert>
    <v-alert v-if="errStatus===403" type="error" class="mb-4">403 — Solo ADMIN (BR-CIE-01)</v-alert>
    <v-skeleton-loader v-if="loading" type="card" />
    <template v-else>
      <v-alert v-if="alreadyClosed" type="info" class="mb-4">Caja ya cerrada para hoy</v-alert>
      <v-card class="mb-4">
        <v-card-title>Preview — totales del día</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="6" md="2"><strong>EFECTIVO</strong><div>${{ totals.EFECTIVO }}</div></v-col>
            <v-col cols="6" md="2"><strong>BILLETERAS</strong><div>${{ totals.BILLETERAS_VIRTUALES }}</div></v-col>
            <v-col cols="6" md="2"><strong>TARJETAS</strong><div>${{ totals.TARJETAS }}</div></v-col>
            <v-col cols="6" md="3"><strong>ENTREGADOS</strong><div>{{ totals.TOTAL_ENTREGADOS }}</div></v-col>
            <v-col cols="6" md="3"><strong>RECHAZADOS</strong><div>{{ totals.TOTAL_RECHAZADOS }}</div></v-col>
          </v-row>
          <v-alert v-if="closeErr" type="error" density="compact" class="mt-4">{{ closeErr }}</v-alert>
        </v-card-text>
        <v-card-actions><v-btn color="primary" :disabled="!isAdmin || alreadyClosed" :loading="closing" @click="doClose">Cerrar caja</v-btn></v-card-actions>
      </v-card>
      <v-card v-if="ticket" title="Ticket payload (JSONB)">
        <v-card-text><pre style="white-space:pre-wrap;word-break:break-all">{{ JSON.stringify(ticket, null, 2) }}</pre></v-card-text>
      </v-card>
    </template>
  </v-container>
</template>
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useCashPreview, useCloseCash, cashErrStatus, cashErrMsg } from '@/composables/useCashClose'
import { useAuthStore } from '@/stores/auth.store'
import { hasAnyRole } from '@/utils/guards'
const auth = useAuthStore()
const isAdmin = computed(()=> hasAnyRole(auth.roles, ['ADMIN']))
const { data, isLoading: loading, error } = useCashPreview()
const errStatus = computed(()=> error.value ? cashErrStatus(error.value) : undefined)
const preview = computed(()=> data.value as { totals: { EFECTIVO: string; BILLETERAS_VIRTUALES: string; TARJETAS: string; TOTAL_ENTREGADOS: number; TOTAL_RECHAZADOS: number }; ticket_payload: Record<string,unknown>; already_closed?: boolean } | undefined)
const totals = computed(()=> preview.value?.totals ?? { EFECTIVO:'0.00', BILLETERAS_VIRTUALES:'0.00', TARJETAS:'0.00', TOTAL_ENTREGADOS:0, TOTAL_RECHAZADOS:0 })
const ticket = computed(()=> preview.value?.ticket_payload ?? null)
const alreadyClosed = computed(()=> !!preview.value?.already_closed)
const closing=ref(false); const closeErr=ref('')
const closeM=useCloseCash()
async function doClose(){
  if(!isAdmin.value) return
  if(!confirm('¿Cerrar caja del día? Esta acción es inmutable.')) return
  closing.value=true; closeErr.value=''
  try{ await closeM.mutateAsync(undefined as never) } catch(e:unknown){ const s=cashErrStatus(e); closeErr.value = s===403 ? '403 — Solo ADMIN puede cerrar (BR-CIE-01)' : s===409 ? '409 — Caja ya cerrada para esta fecha' : cashErrMsg(e) }
  finally{ closing.value=false }
}
</script>
