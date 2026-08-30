<template>
  <v-list density="compact" nav>
    <v-list-item :active="!cat" title="Todos" @click="go()" />
    <v-list-item v-for="c in cats" :key="c.id" :active="cat===c.id" :title="c.name" @click="go(c.id)" />
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
function go(id?: number) {
  router.push({ query: { ...route.query, category: id ? String(id) : undefined, search: route.query.search as string | undefined } })
}
</script>
