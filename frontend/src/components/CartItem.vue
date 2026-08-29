<template>
  <v-card variant="tonal" class="mb-2 pa-2">
    <div class="d-flex justify-space-between align-center">
      <div><strong>{{ item.product.name }}</strong> × {{ item.qty }} — ${{ item.product.price }}</div>
      <v-btn icon="mdi-delete" size="x-small" variant="text" @click="cart.remove(item.uid)" />
    </div>
    <div v-if="item.flavorNames.length" class="text-caption mt-1">{{ item.flavorNames.join(', ') }}</div>
    <div class="d-flex ga-1 mt-2">
      <v-btn size="x-small" icon="mdi-minus" @click="cart.dec(item.uid)" />
      <v-btn size="x-small" icon="mdi-plus" @click="cart.inc(item.uid)" />
    </div>
  </v-card>
</template>
<script setup lang="ts">
import { useCartStore } from '@/stores/cart.store'
defineProps<{ item: any }>()
const cart = useCartStore()
</script>
