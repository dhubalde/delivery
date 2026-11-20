<template>
  <v-chip :color="color" size="small" variant="tonal">{{ label }}</v-chip>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { statusColors } from '@/design/tokens'

/**
 * The only way a boolean state is rendered as a chip.
 * Positive states are green (`statusColors.positive`); negative ones stay neutral
 * so green keeps meaning "works / is on".
 */
const props = withDefaults(
  defineProps<{
    value: boolean | string
    positive?: string
    negative?: string
    positiveColor?: string
    negativeColor?: string
  }>(),
  {
    positive: 'Sí',
    negative: 'No',
    positiveColor: statusColors.positive,
    negativeColor: statusColors.neutral,
  },
)

const isPositive = computed(
  () => props.value === true || (typeof props.value === 'string' && props.value === props.positive),
)
const color = computed(() => (isPositive.value ? props.positiveColor : props.negativeColor))
const label = computed(() => (isPositive.value ? props.positive : props.negative))
</script>
