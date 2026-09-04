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
        <div class="totals-centered">
          <div class="total-item">
            <span class="total-label">Efectivo</span>
            <strong class="total-amount" :class="{ 'small-amount': hasAnyLarge }">${{ fmt(display.efectivo) }}</strong>
          </div>
          <div class="total-item">
            <span class="total-label">Billeteras</span>
            <strong class="total-amount" :class="{ 'small-amount': hasAnyLarge }">${{ fmt(display.billeteras) }}</strong>
          </div>
          <div class="total-item">
            <span class="total-label">Tarjetas</span>
            <strong class="total-amount" :class="{ 'small-amount': hasAnyLarge }">${{ fmt(display.tarjetas) }}</strong>
          </div>
          <v-divider class="my-2" />
          <div class="total-item total-item--total">
            <span class="total-label font-weight-bold">Total</span>
            <strong class="total-amount total-amount--big" :class="{ 'small-amount': hasAnyLarge }">${{ fmt(display.total) }}</strong>
          </div>
        </div>
        <div v-if="isFallback" class="text-caption text-medium-emphasis mt-2 text-center">* estimado local (ENTREGADO)</div>
        <div v-if="isError && !hasPreview" class="text-caption text-medium-emphasis mt-2 text-center">Sin preview — usando cálculo local</div>
      </div>
    </v-card-text>
  </v-card>
</template>
<script setup lang="ts">
import { computed, toRef } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { cashApi } from '@/api/panel/cash.api'
import { qk } from '@/queries/keys'
import { INTERVALS } from '@/queries/intervals'

type FallbackPayment = { method: string; status: string; amount?: string }
type FallbackOrder = { total: string; payments: FallbackPayment[] }

const props = defineProps<{ fallbackOrders: FallbackOrder[]; businessDate?: string }>()
const businessDateRef = toRef(props, 'businessDate')

const { data, isLoading, isError } = useQuery({
  queryKey: computed(() => qk.adminCashPreview(businessDateRef.value)),
  queryFn: () => cashApi.preview(businessDateRef.value),
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
    if (!pays.length) {
      const tot = parseFloat(o.total ?? '0')
      if (!Number.isNaN(tot) && tot !== 0) efectivo += tot
      continue
    }
    let orderHasValid = false
    for (const p of pays) {
      if (p.status === 'REJECTED') continue
      if (p.status === 'PENDING' && p.method === 'EFECTIVO') continue
      const amt = p.amount != null ? parseFloat(p.amount) : 0
      if (Number.isNaN(amt) || amt === 0) continue
      orderHasValid = true
      if (p.method === 'EFECTIVO') efectivo += amt
      else if (p.method === 'BILLETERA' || p.method === 'BILLETERAS_VIRTUALES' || p.method === 'BILLETERAS') billeteras += amt
      else if (p.method === 'TARJETA' || p.method === 'TARJETAS') tarjetas += amt
    }
    if (!orderHasValid) {
      const tot = parseFloat(o.total ?? '0')
      if (!Number.isNaN(tot) && tot !== 0) efectivo += tot
    }
  }
  return { efectivo, billeteras, tarjetas, total: efectivo + billeteras + tarjetas }
})

const display = computed(() => previewDisplay.value ?? fallbackDisplay.value)
const isFallback = computed(() => !previewDisplay.value)
const isLarge = computed(() => (display.value?.total ?? 0) >= 1_000_000)
const hasAnyLarge = computed(() => {
  const d = display.value
  if (!d) return false
  return d.efectivo >= 1_000_000 || d.billeteras >= 1_000_000 || d.tarjetas >= 1_000_000 || d.total >= 1_000_000
})

function fmt(n: number) {
  return n.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<style scoped>
.totals-centered {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.total-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 2px;
}
.total-label {
  font-size: 0.85rem;
  color: rgba(0, 0, 0, 0.6);
  letter-spacing: 0.02em;
}
.total-amount {
  font-size: 1.05rem;
  font-weight: 600;
  line-height: 1.2;
  word-break: break-all;
  max-width: 100%;
}
.total-amount--big {
  font-size: 1.25rem;
  font-weight: 700;
  color: #06B6D4;
}
.small-amount {
  font-size: 0.88rem !important;
  letter-spacing: -0.02em;
}
.total-item--total .small-amount {
  font-size: 1rem !important;
}
</style>
