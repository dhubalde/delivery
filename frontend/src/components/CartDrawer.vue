<template>
  <v-card>
    <v-card-title class="d-flex justify-space-between">Carrito <v-chip size="small">{{ cart.count }}</v-chip></v-card-title>
    <v-card-text>
      <v-skeleton-loader v-if="loading" type="list-item@3" />
      <v-alert v-else-if="cart.isEmpty" type="info" variant="tonal">Carrito vacío</v-alert>
      <template v-else>
        <CartItem v-for="it in cart.items" :key="it.uid" :item="it" />
        <v-divider class="my-2" />
        <div class="font-weight-bold">Total: ${{ cart.total.toFixed(2) }}</div>
        <v-alert v-if="inlineError" type="error" variant="tonal" class="mt-2">{{ inlineError }}</v-alert>
        <v-btn block color="primary" class="mt-2" :disabled="cart.isEmpty || closed" :to="checkoutTo">Ir a pagar</v-btn>
        <div v-if="closed" class="text-caption text-warning mt-1">Cerrado — no se puede comprar</div>
      </template>
    </v-card-text>
  </v-card>
  <MyOrders />
</template>
<script setup lang="ts">
import { computed, watch } from 'vue'
import { useCartStore } from '@/stores/cart.store'
import { useMenu } from '@/composables/useMenu'
import CartItem from '@/components/CartItem.vue'
import MyOrders from '@/components/MyOrders.vue'
const props = defineProps<{ loading?: boolean; inlineError?: string | null; slug?: string }>()
const cart = useCartStore()
const routeSlug = computed(() => {
  if (props.slug) return props.slug
  try {
    const path = window.location.pathname || ''
    const m = path.match(/^\/([^\/]+)/)
    if (m && m[1] && !['panel', 'master', 'login', 'change-password'].includes(m[1])) return m[1]
  } catch {}
  return 'ice-zone'
})
watch(
  routeSlug,
  (s) => cart.setSlug(s),
  { immediate: true },
)
const { data } = useMenu(routeSlug as any) as any
const closed = computed(() => {
  const d = (data as any).value as any
  if (!d) return false
  return d.closed === true || d.is_open === false || d.isOpen === false
})
const checkoutTo = computed(() => `/${routeSlug.value}/checkout`)
</script>
