<template>
  <div id="printable-ticket" class="ticket">
    <div class="ticket-header">
      <h3 style="font-family:Comfortaa">ICE ZONE — Cierre de caja</h3>
      <div class="text-caption text-medium-emphasis">{{ ticket.business_date }} — {{ ticket.merchant_slug }}</div>
      <div class="text-caption">Cajero: {{ ticket.cashier_name }} (#{{ ticket.cashier_id }})</div>
      <div v-if="ticket.closed_at" class="text-caption">Cierre: {{ ticket.closed_at }}</div>
    </div>
    <v-divider class="my-3" />
    <div class="ticket-body">
      <div class="row"><span>EFECTIVO</span><strong>${{ totals.EFECTIVO }}</strong></div>
      <div class="row"><span>BILLETERAS VIRTUALES</span><strong>${{ totals.BILLETERAS_VIRTUALES }}</strong></div>
      <div class="row"><span>TARJETAS</span><strong>${{ totals.TARJETAS }}</strong></div>
      <v-divider class="my-2" />
      <div class="row"><span>ENTREGADOS</span><strong>{{ totals.TOTAL_ENTREGADOS }}</strong></div>
      <div class="row"><span>RECHAZADOS</span><strong>{{ totals.TOTAL_RECHAZADOS }}</strong></div>
    </div>
    <div class="ticket-footer text-caption text-medium-emphasis mt-4">
      Ticket generado el {{ now }} — inmutable (BR-CIE-01)
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ ticket: Record<string,unknown> }>()
const totals = computed(()=> (props.ticket?.totals as Record<string,unknown> ?? {}) as { EFECTIVO:string; BILLETERAS_VIRTUALES:string; TARJETAS:string; TOTAL_ENTREGADOS:number; TOTAL_RECHAZADOS:number })
const now = new Date().toLocaleString('es-AR')
</script>
<style scoped>
.ticket { font-family: monospace; max-width: 320px; margin: 0 auto; padding: 16px; border: 1px dashed #999; background: white; }
.ticket-header h3 { margin:0 0 4px 0; font-size: 14px; }
.row { display:flex; justify-content:space-between; padding:4px 0; font-size: 13px; }
@media print {
  :global(body * ) { visibility: hidden; }
  #printable-ticket, #printable-ticket * { visibility: visible; }
  #printable-ticket { position: absolute; left:0; top:0; width:100%; border:none; }
}
</style>
