<template>
  <v-card>
    <v-img :src="img" height="140" cover loading="lazy" />
    <v-card-title class="text-body-2" style="font-family:Comfortaa">{{ p.name }}</v-card-title>
    <v-card-text>
      <div class="d-flex align-center ga-2">
        <v-chip v-if="badge" size="x-small" color="primary">{{ badge }}</v-chip>
        <span class="font-weight-bold">${{ priceFormatted }}</span>
      </div>
      <div v-if="needsFlavors" class="mt-2">
        <div class="text-caption text-center text-medium-emphasis">{{ hint }}</div>
      </div>
    </v-card-text>
    <v-card-actions><v-btn size="small" color="primary" :disabled="!p.is_active" @click="add">Agregar</v-btn></v-card-actions>
  </v-card>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useCartStore } from '@/stores/cart.store'
import { toast } from '@/composables/useConfirm'
const props = defineProps<{ p: any }>()
const cart = useCartStore()
const badge = computed(() => ({ KG_1: '1 kg', KG_HALF: '1/2 kg', KG_QUARTER: '1/4 kg' } as Record<string, string>)[props.p.pote_size] ?? null)
const priceFormatted = computed(() => Number(props.p.price).toFixed(2))
const needsFlavors = computed(() => {
  if (props.p.min_flavors == null || props.p.max_flavors == null) return false
  if (props.p.product_type === 'POTE' && !!props.p.pote_size) return true
  return props.p.min_flavors != null && props.p.max_flavors != null
})
const hint = computed(() => {
  if (!needsFlavors.value) return ''
  if (props.p.min_flavors != null && props.p.max_flavors != null) {
    return props.p.min_flavors === props.p.max_flavors ? `Elige ${props.p.min_flavors} gustos` : `Elige ${props.p.min_flavors} a ${props.p.max_flavors} gustos`
  }
  return ''
})
const img = computed(() => props.p.image_url || `/placeholders/${pick()}.jpg`)
function pick() { const m: Record<string, string> = { KG_1: 'pote-1kg', KG_HALF: 'pote-medio', KG_QUARTER: 'pote-cuarto' }; return m[props.p.pote_size] ?? 'pote-1kg' }
function add() {
  try {
    cart.add(props.p, [], [])
  } catch (e: any) {
    toast(e?.message ?? 'Error al agregar', 'error')
  }
}
</script>
