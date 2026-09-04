<template>
  <ProductGrid :items="(products as any[])" :loading="isLoading" />
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProducts } from '@/composables/useProducts'
import { useAuthStore } from '@/stores/auth.store'
import ProductGrid from '@/components/ProductGrid.vue'
const route = useRoute()
const auth = useAuthStore()
const slug = computed(() => auth.merchantSlug || 'ice-zone')
const category = computed(() => route.query.category ? Number(route.query.category) : undefined)
const search = computed(() => (route.query.search as string) || undefined)
const { data: products = [], isLoading } = useProducts(slug, category, search) as any
</script>