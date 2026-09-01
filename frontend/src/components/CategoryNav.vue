<template>
  <v-list density="compact" nav>
    <v-list-item :active="!cat" title="Todos" prepend-icon="mdi-apps" @click="go()" />
    <v-list-item v-for="c in cats" :key="c.id" :active="cat===c.id" :title="c.name" :prepend-icon="iconFor(c.name)" @click="go(c.id)" />
  </v-list>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'
import { useCategories } from '@/composables/useProducts'
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const slug = computed(() => auth.merchantSlug || 'ice-zone')
const { data: categories } = useCategories(slug) as any
const cats = computed(() => (categories.value as any[] | undefined) ?? [])
const cat = computed(() => route.query.category ? Number(route.query.category) : undefined)
function iconFor(name: string): string {
  const n = name.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim()
  if (n.includes('helad')) return 'mdi-ice-cream'
  if (n.includes('postre')) return 'mdi-cupcake'
  if (n.includes('torta')) return 'mdi-cake-variant'
  if (n.includes('tarta')) return 'mdi-fruit-cherries'
  if (n.includes('alfajor')) return 'mdi-cookie'
  if (n.includes('cafe')) return 'mdi-coffee'
  if (n.includes('pote')) return 'mdi-ice-cream'
  if (n.includes('bombon')) return 'mdi-candy'
  if (n.includes('cono')) return 'mdi-ice-cream-outline'
  return 'mdi-shape-outline'
}
function go(id?: number) {
  router.push({ query: { ...route.query, category: id ? String(id) : undefined, search: route.query.search as string | undefined } })
}
</script>
