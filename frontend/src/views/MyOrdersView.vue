<template>
  <v-container>
    <h2 class="text-h6 mb-4">Mis pedidos — {{ slug }}</h2>
    <MyOrders />
    <v-btn :to="`/${slug}`" color="primary" variant="tonal" class="mt-4">Volver al catálogo</v-btn>
  </v-container>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import MyOrders from '@/components/MyOrders.vue'
const route = useRoute()
const slug = computed(() => (route.params.slug as string) || 'ice-zone')
</script>
