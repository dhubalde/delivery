<template>
  <v-card class="mb-4">
    <v-card-title class="text-subtitle-2 d-flex align-center ga-2">
      Ventas por día
      <span v-if="monthLabel" class="text-caption font-weight-bold" style="color: #06B6D4">{{ monthLabel }}</span>
      <v-spacer />
      <span class="text-caption text-medium-emphasis">Total rango: ${{ fmt(rangeTotal) }}</span>
    </v-card-title>
    <v-card-text>
      <div v-if="!days.length" class="text-caption text-medium-emphasis">Sin ventas en el rango</div>
      <svg v-else :viewBox="`0 0 ${width} ${height}`" style="width: 100%; height: auto; display: block" role="img" aria-label="Ventas por día">
        <line :x1="padL" :y1="height - padB" :x2="width - padR" :y2="height - padB" stroke="rgba(0,0,0,.2)" />
        <g v-for="(d, i) in days" :key="d.date">
          <rect
            :x="barX(i)"
            :y="barY(valueOf(d))"
            :width="barW"
            :height="barH(valueOf(d))"
            rx="3"
            fill="#06B6D4"
            :opacity="valueOf(d) === maxTotal ? 1 : 0.65"
          >
            <title>{{ fullDate(d.date) }}: ${{ fmt(valueOf(d)) }}</title>
          </rect>
          <text :x="barX(i) + barW / 2" :y="barY(valueOf(d)) - 4" text-anchor="middle" font-size="9" fill="rgba(0,0,0,.7)">
            {{ shortValue(valueOf(d)) }}
          </text>
          <text :x="barX(i) + barW / 2" :y="height - padB + 13" text-anchor="middle" font-size="7.5" fill="rgba(0,0,0,.6)">
            {{ shortDate(d.date) }}
          </text>
        </g>
      </svg>
      <div class="d-flex ga-4 mt-2 text-caption text-medium-emphasis">
        <span><v-icon icon="mdi-square" size="12" color="#06B6D4" /> Total vendido</span>
        <span>Ticket prom. rango: ${{ fmt(avgTicket) }}</span>
      </div>
    </v-card-text>
  </v-card>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import type { CashDailyDay } from '@/api/panel/cash.api'

const props = withDefaults(defineProps<{ days?: CashDailyDay[] }>(), { days: () => [] })

const width = 640
const height = 150
const padL = 8
const padR = 8
const padB = 26
const padT = 18

const days = computed(() => props.days ?? [])
const valueOf = (d: CashDailyDay) => Number.parseFloat(d.TOTAL ?? '0') || 0
const maxTotal = computed(() => Math.max(0, ...days.value.map(valueOf)))
const rangeTotal = computed(() => days.value.reduce((a, d) => a + valueOf(d), 0))
const totalEntregados = computed(() => days.value.reduce((a, d) => a + (Number(d.TOTAL_ENTREGADOS ?? 0) || 0), 0))
const avgTicket = computed(() => (totalEntregados.value > 0 ? rangeTotal.value / totalEntregados.value : 0))

const slot = computed(() => (width - padL - padR) / Math.max(days.value.length, 1))
const barW = computed(() => Math.max(8, Math.min(44, slot.value * 0.55)))
const barX = (i: number) => padL + slot.value * i + (slot.value - barW.value) / 2
const plotH = height - padT - padB
const barY = (v: number) => (maxTotal.value > 0 ? height - padB - (v / maxTotal.value) * plotH : height - padB)
const barH = (v: number) => (maxTotal.value > 0 ? Math.max(v > 0 ? 2 : 0, (v / maxTotal.value) * plotH) : 0)

function shortDate(iso: string): string {
  return String(Number(iso.split('-')[2]))
}
const MONTHS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
const monthLabel = computed(() => {
  if (!days.value.length) return ''
  const first = days.value[0].date.split('-')
  const last = days.value[days.value.length - 1].date.split('-')
  const sameMonth = first[0] === last[0] && first[1] === last[1]
  if (sameMonth) return `${MONTHS[Number(first[1]) - 1]} ${first[0]}`
  return `${Number(first[2])} ${MONTHS[Number(first[1]) - 1]} — ${Number(last[2])} ${MONTHS[Number(last[1]) - 1]} ${last[0]}`
})
function fullDate(iso: string): string {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}
function fmt(n: number): string {
  return n.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function shortValue(v: number): string {
  if (v >= 1_000_000) return `${(v / 1_000_000).toLocaleString('es-AR', { maximumFractionDigits: 1 })}M`
  if (v >= 1000) return `${(v / 1000).toLocaleString('es-AR', { maximumFractionDigits: 1 })}k`
  return v === 0 ? '' : String(Math.round(v))
}
</script>
