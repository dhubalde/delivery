<template>
  <v-alert v-if="closed" type="warning" variant="tonal" class="mb-3">
    Cerrado<span v-if="nextAt"> — abre {{ nextAt }}</span>
  </v-alert>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useMenu } from '@/composables/useMenu'
import { useAuthStore } from '@/stores/auth.store'
const auth = useAuthStore()
const { data } = useMenu(computed(() => auth.merchantSlug || 'ice-zone') as any) as any
const closed = computed(() => {
  const d = data.value as any
  if (!d) return false
  if (d.closed === true) return true
  if (d.is_open === false) return true
  if (d.isOpen === false) return true
  return false
})
const nextAt = computed(() => {
  const d = data.value as any
  if (!d?.next_open_at) return null
  try { return new Date(d.next_open_at).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }) } catch { return d.next_open_at }
})
</script>
