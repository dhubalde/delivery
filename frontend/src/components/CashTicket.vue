<template>
  <div class="ticket">
    <div class="ticket-header">
      <h3 style="font-family:Comfortaa">ICE ZONE — Cierre de caja</h3>
      <div class="text-caption text-medium-emphasis">{{ ticket.business_date }} — {{ ticket.merchant_slug }}</div>
      <div class="text-caption">Cajero: {{ ticket.cashier_name }} (#{{ ticket.cashier_id }})</div>
      <div v-if="ticket.closed_at" class="text-caption">Cierre: {{ ticket.closed_at }}</div>
    </div>
    <v-divider class="my-3" />
    <div class="ticket-body">
      <div class="row"><span>EFECTIVO</span><strong>${{ fmt(totals.EFECTIVO) }}</strong></div>
      <div class="row"><span>BILLETERAS VIRTUALES</span><strong>${{ fmt(totals.BILLETERAS_VIRTUALES) }}</strong></div>
      <div class="row"><span>TARJETAS</span><strong>${{ fmt(totals.TARJETAS) }}</strong></div>
      <div class="row total"><span>TOTAL</span><strong>${{ totalImporte }}</strong></div>
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
const totals = computed(()=> (props.ticket?.totals as Record<string,unknown> ?? {}) as { EFECTIVO:string; BILLETERAS_VIRTUALES:string; TARJETAS:string; TOTAL?:string | null; TOTAL_ENTREGADOS:number; TOTAL_RECHAZADOS:number })
const fmt = (v: unknown) => {
  const n = Number.parseFloat(String(v ?? 0))
  return Number.isNaN(n) ? '0.00' : n.toFixed(2)
}
const totalImporte = computed(()=>{
  const t = totals.value.TOTAL
  const pn = t != null && String(t).trim() !== '' ? Number.parseFloat(String(t)) : Number.NaN
  if (!Number.isNaN(pn)) return pn.toFixed(2)
  const e = Number.parseFloat(String(totals.value.EFECTIVO ?? 0))
  const b = Number.parseFloat(String(totals.value.BILLETERAS_VIRTUALES ?? 0))
  const c = Number.parseFloat(String(totals.value.TARJETAS ?? 0))
  const sum = (Number.isNaN(e) ? 0 : e) + (Number.isNaN(b) ? 0 : b) + (Number.isNaN(c) ? 0 : c)
  return sum.toFixed(2)
})
const now = new Date().toLocaleString('es-AR')
</script>
<style scoped>
.ticket { font-family: monospace; max-width: 320px; margin: 0 auto; padding: 16px; border: 1px dashed #999; background: white; color: #000; }
.ticket-header h3 { margin:0 0 4px 0; font-size: 14px; color: #000; }
.row { display:flex; justify-content:space-between; padding:4px 0; font-size: 13px; color: #000; }
.row.total { font-weight: 700; border-top: 2px solid #000; margin-top: 4px; padding-top: 8px; }
.ticket .text-caption { color: #000 !important; }
.ticket .text-medium-emphasis { color: rgba(0,0,0,0.6) !important; opacity: 1 !important; }
</style>
