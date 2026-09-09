<template>
  <div class="app-logo" :style="{ width: size + 'px', height: (size * 0.22) + 'px' }" :class="variant">
    <img v-if="merchantLogo" :src="merchantLogo" :alt="alt" :width="size" :height="Math.round(size*0.22)" style="object-fit:contain;max-width:100%;" />
    <svg v-else xmlns="http://www.w3.org/2000/svg" :viewBox="`0 0 ${withText ? 200 : 44} 44`" :width="withText ? size : Math.round(size*0.22)" :height="Math.round(size*0.22)" role="img" :aria-label="alt">
      <text x="22" y="22" text-anchor="middle" dominant-baseline="central" font-family="Comfortaa, sans-serif" font-size="26" font-weight="700" :fill="graphiteColor">W</text>
      <text v-if="withText" x="46" y="27.5" font-family="Comfortaa, sans-serif" font-size="18.5" font-weight="700" letter-spacing="0.04em">
        <tspan :fill="graphiteColor">WORK</tspan><tspan :fill="graphiteColor" dx="6">ZONE</tspan>
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
  alt: 'Work Zone',
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

const graphiteColor = computed(() => {
  if (props.variant === 'dark') return '#E5E7EB'
  if (props.variant === 'light') return '#2D2D2D'
  return ui.theme === 'dark' ? '#E5E7EB' : '#2D2D2D'
})

const zoneColor = graphiteColor
</script>
