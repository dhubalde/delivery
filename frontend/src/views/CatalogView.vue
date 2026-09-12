<template>
  <NotFoundView v-if="isNotFound" />
  <ProductGrid v-else :items="(products as any[])" :loading="isLoading" />
</template>
<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useCatalog } from '@/composables/useCatalog'
import { useCartStore } from '@/stores/cart.store'
import { useCustomerStore } from '@/stores/customer.store'
import ProductGrid from '@/components/ProductGrid.vue'
import NotFoundView from '@/views/NotFoundView.vue'

const route = useRoute()
const slug = computed(() => (route.params.slug as string) || 'ice-zone')
const category = computed(() => (route.query.category ? Number(route.query.category) : undefined))
const search = computed(() => (route.query.search as string) || undefined)

const cart = useCartStore()
const customer = useCustomerStore()

watch(
  slug,
  (s) => {
    cart.setSlug(s)
    customer.hydrate(s)
  },
  { immediate: true },
)

const { data: aggregate, isLoading, error } = useCatalog(slug) as any

const isNotFound = computed(() => {
  const err: any = error?.value
  if (!err) return false
  const status = err?.response?.status || err?.status
  return status === 404
})

const products = computed(() => {
  const agg: any = aggregate?.value
  if (!agg) return []
  let list: any[] = Array.isArray(agg.products) ? agg.products : []
  if (category.value != null) {
    list = list.filter((p: any) => p.category === category.value || p.category_id === category.value)
  }
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter((p: any) => String(p.name || '').toLowerCase().includes(q))
  }
  return list
})
</script>