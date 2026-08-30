<template>
  <v-card :style="{ borderTop: `4px solid #06B6D4` }" style="min-height: 420px">
    <v-card-title style="background-color: #06B6D4; color: white" class="text-subtitle-2">
      Totales del día
    </v-card-title>
    <v-divider />
    <v-card-text>
      <div v-if="isLoading" class="d-flex flex-column ga-2">
        <v-skeleton-loader type="text" />
        <v-skeleton-loader type="text" />
        <v-skeleton-loader type="text" />
      </div>
      <div v-else>
        <div class="d-flex justify-space-between py-1 text-body-2">
          <span>Efectivo</span><strong>${{ fmt(display.efectivo) }}</strong>
        </div>
        <div class="d-flex justify-space-between py-1 text-body-2">
          <span>Billeteras</span><strong>${{ fmt(display.billeteras) }}</strong>
        </div>
        <div class="d-flex justify-space-between py-1 text-body-2">
          <span>Tarjetas</span><strong>${{ fmt(display.tarjetas) }}</strong>
        </div>
        <v-divider class="my-2" />
        <div class="d-flex justify-space-between py-1 text-body-2 font-weight-bold">
          <span>Total</span><span>${{ fmt(display.total) }}</span>
        </div>
        <div v-if="isFallback" class="text-caption text-medium-emphasis mt-2">* estimado local (ENTREGADO)</div>
        <div v-if="isError && !hasPreview" class="text-caption text-medium-emphasis mt-2">Sin preview — usando cálculo local</div>
      </div>
    </v-card-text>
  </v-card>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { cashApi } from '@/api/panel/cash.api'
import { qk } from '@/queries/keys'
import { INTERVALS } from '@/queries/intervals'

type FallbackPayment = { method: string; status: string; amount?: string }
type FallbackOrder = { total: string; payments: FallbackPayment[] }

const props = defineProps<{ fallbackOrders: FallbackOrder[] }>()

const { data, isLoading, isError } = useQuery({
  queryKey: qk.adminCashPreview(),
  queryFn: cashApi.preview,
  retry: false,
  refetchInterval: INTERVALS.BOARD,
  staleTime: 0,
  refetchOnWindowFocus: true,
})

const hasPreview = computed(() => !!data.value?.totals)

const previewDisplay = computed(() => {
  const t = data.value?.totals
  if (!t) return null
  const e = parseFloat(t.EFECTIVO ?? '0')
  const b = parseFloat(t.BILLETERAS_VIRTUALES ?? '0')
  const ta = parseFloat(t.TARJETAS ?? '0')
  return { efectivo: e, billeteras: b, tarjetas: ta, total: e + b + ta }
})

const fallbackDisplay = computed(() => {
  let efectivo = 0
  let billeteras = 0
  let tarjetas = 0
  for (const o of props.fallbackOrders ?? []) {
    const pays = o.payments ?? []
    if (!pays.length) continue
    for (const p of pays) {
      if (p.status === 'REJECTED') continue
      if (p.status === 'PENDING' && p.method === 'EFECTIVO') continue
      const amt = p.amount != null ? parseFloat(p.amount) : 0
      if (Number.isNaN(amt) || amt === 0) continue
      if (p.method === 'EFECTIVO') efectivo += amt
      else if (p.method === 'BILLETERA' || p.method === 'BILLETERAS_VIRTUALES' || p.method === 'BILLETERAS') billeteras += amt
      else if (p.method === 'TARJETA' || p.method === 'TARJETAS') tarjetas += amt
    }
  }
  if (efectivo === 0 && billeteras === 0 && tarjetas === 0 && props.fallbackOrders?.length) {
    for (const o of props.fallbackOrders) {
      const tot = parseFloat(o.total ?? '0')
      if (Number.isNaN(tot)) continue
      efectivo += 0
      void tot
    }
  }
  return { efectivo, billeteras, tarjetas, total: efectivo + billeteras + tarjetas }
})

const display = computed(() => previewDisplay.value ?? fallbackDisplay.value)
const isFallback = computed(() => !previewDisplay.value)

function fmt(n: number) {
  return n.toFixed(2)
}
</script>
