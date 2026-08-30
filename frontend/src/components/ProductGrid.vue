<template>
  <div v-if="loading" class="d-flex flex-column ga-2">
    <v-skeleton-loader v-for="n in 6" :key="n" type="list-item-avatar" />
  </div>
  <v-alert v-else-if="!items.length" type="info" variant="tonal">Sin resultados</v-alert>
  <v-list v-else density="compact" class="py-0">
    <ProductCard v-for="p in items" :key="p.id" :p="p" />
  </v-list>
</template>
<script setup lang="ts">
import ProductCard from '@/components/ProductCard.vue'
defineProps<{ items: any[]; loading: boolean }>()
</script>
