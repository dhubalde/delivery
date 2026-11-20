<template>
  <div class="d-flex align-center justify-space-between mb-3 flex-wrap ga-2">
    <div>
      <h2 class="text-h6 mb-1" :style="{ fontFamily: titleFont }">{{ title }}</h2>
      <div v-if="subtitle" class="text-caption text-medium-emphasis">{{ subtitle }}</div>
    </div>
    <div class="d-flex align-center ga-2 flex-wrap justify-end">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { titleFont } from '@/design/tokens'

defineProps<{ title: string; subtitle?: string }>()
</script>
