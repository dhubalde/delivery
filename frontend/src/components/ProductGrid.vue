<template>
  <div v-if="loading" class="d-flex flex-wrap ga-4">
    <v-skeleton-loader v-for="n in 6" :key="n" type="card" width="300" />
  </div>
  <v-alert v-else-if="!items.length" type="info" variant="tonal">Sin resultados</v-alert>
  <v-row v-else>
    <v-col v-for="p in items" :key="p.id" cols="12" sm="6" md="4" lg="4">
      <ProductCard :p="p" />
    </v-col>
  </v-row>
</template>
<script setup lang="ts">
import ProductCard from '@/components/ProductCard.vue'
defineProps<{ items: any[]; loading: boolean }>()
</script>
