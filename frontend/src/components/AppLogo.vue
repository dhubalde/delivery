<template>
  <div class="app-logo" :style="{ width: size + 'px', height: (size * 0.22) + 'px' }" :class="variant">
    <img v-if="merchantLogo" :src="merchantLogo" :alt="alt" :width="size" :height="Math.round(size*0.22)" style="object-fit:contain;max-width:100%;" />
    <svg v-else xmlns="http://www.w3.org/2000/svg" :viewBox="`0 0 ${withText ? 200 : 44} 44`" :width="withText ? size : Math.round(size*0.22)" :height="Math.round(size*0.22)" role="img" :aria-label="alt">
      <g transform="translate(22,22)">
        <line x1="0" y1="-13.5" x2="0" y2="13.5" stroke="#06B6D4" stroke-width="2.6" stroke-linecap="round" />
        <line x1="-11.7" y1="-6.75" x2="11.7" y2="6.75" stroke="#06B6D4" stroke-width="2.6" stroke-linecap="round" />
        <line x1="-11.7" y1="6.75" x2="11.7" y2="-6.75" stroke="#06B6D4" stroke-width="2.6" stroke-linecap="round" />
        <circle cx="0" cy="0" r="3.3" fill="#06B6D4" />
        <circle cx="0" cy="-13.5" r="1.7" fill="#06B6D4" />
        <circle cx="0" cy="13.5" r="1.7" fill="#06B6D4" />
        <circle cx="-11.7" cy="-6.75" r="1.7" fill="#06B6D4" />
        <circle cx="11.7" cy="6.75" r="1.7" fill="#06B6D4" />
        <circle cx="-11.7" cy="6.75" r="1.7" fill="#06B6D4" />
        <circle cx="11.7" cy="-6.75" r="1.7" fill="#06B6D4" />
      </g>
      <text v-if="withText" x="46" y="27.5" font-family="Comfortaa, sans-serif" font-size="18.5" font-weight="700" letter-spacing="0.04em">
        <tspan fill="#06B6D4">ICE</tspan><tspan :fill="zoneColor" dx="6">ZONE</tspan>
      </text>
    </svg>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useMerchant } from '@/composables/useMerchant'
import { useUiStore } from '@/stores/ui.store'

const props = withDefaults(defineProps<{
  size?: number
  variant?: 'light' | 'dark' | 'auto'
  withText?: boolean
  alt?: string
  forceDefault?: boolean
}>(), {
  size: 160,
  variant: 'auto',
  withText: true,
  alt: 'Ice Zone',
  forceDefault: false,
})

const ui = useUiStore()
const { data: merchant } = useMerchant()

const merchantLogo = computed(() => {
  if (props.forceDefault) return null
  const m = merchant.value as unknown as { logo?: string | null; logo_url?: string | null } | undefined
  if (!m) return null
  return m.logo || m.logo_url || null
})

const zoneColor = computed(() => {
  if (props.variant === 'dark') return '#F8FAFC'
  if (props.variant === 'light') return '#1E293B'
  return ui.theme === 'dark' ? '#F8FAFC' : '#1E293B'
})
</script>
