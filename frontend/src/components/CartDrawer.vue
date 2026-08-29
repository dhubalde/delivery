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
        <v-btn block color="primary" class="mt-2" :disabled="cart.isEmpty || closed" to="/checkout">Ir a pagar</v-btn>
        <div v-if="closed" class="text-caption text-warning mt-1">Cerrado — no se puede comprar</div>
      </template>
    </v-card-text>
  </v-card>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useCartStore } from '@/stores/cart.store'
import { useMenu } from '@/composables/useMenu'
import { useAuthStore } from '@/stores/auth.store'
import CartItem from '@/components/CartItem.vue'
defineProps<{ loading?: boolean; inlineError?: string | null }>()
const cart = useCartStore()
const auth = useAuthStore()
const { data } = useMenu(computed(() => auth.merchantSlug || 'ice-zone') as any) as any
const closed = computed(() => {
  const d = (data as any).value as any
  if (!d) return false
  return d.closed === true || d.is_open === false || d.isOpen === false
})
</script>
