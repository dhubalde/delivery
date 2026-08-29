<template>
  <v-card>
    <v-img :src="img" height="140" cover loading="lazy" />
    <v-card-title class="text-body-2" style="font-family:Comfortaa">{{ p.name }}</v-card-title>
    <v-card-text>
      <v-chip v-if="badge" size="x-small" color="primary" class="mr-1">{{ badge }}</v-chip>
      <span class="font-weight-bold">${{ p.price }}</span>
      <div class="mt-2">
        <v-chip v-for="f in flavors" :key="f" size="x-small" class="mr-1 mb-1">{{ f }}</v-chip>
      </div>
    </v-card-text>
  </v-card>
</template>
<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ p: any }>()
const badge = computed(() => ({ KG_1:'1KG', KG_HALF:'1/2KG', KG_QUARTER:'1/4KG' } as Record<string,string>)[props.p.pote_size] ?? null)
const flavors = computed(() => props.p.flavors ?? props.p.flavor_names ?? [])
const img = computed(() => props.p.image_url || `/placeholders/${pick()}.jpg`)
function pick() {
  const m: Record<string,string> = { KG_1:'pote-1kg', KG_HALF:'pote-medio', KG_QUARTER:'pote-cuarto' }
  return m[props.p.pote_size] ?? 'pote-1kg'
}
</script>
