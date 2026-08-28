<template>
  <v-list density="compact" nav>
    <v-list-item :active="!cat" title="Todos" @click="go()" />
    <v-list-item v-for="c in cats" :key="c.id" :active="cat===c.id" :title="c.name" @click="go(c.id)" />
  </v-list>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
const cats = [{id:1,name:'Helados'},{id:2,name:'Postres'},{id:3,name:'Tortas'},{id:4,name:'Tartas'},{id:5,name:'Alfajores'},{id:6,name:'Cafetería'}]
const route = useRoute()
const router = useRouter()
const cat = computed(() => route.query.category ? Number(route.query.category) : undefined)
function go(id?: number) {
  router.push({ query: { ...route.query, category: id ? String(id) : undefined, search: route.query.search as string | undefined } })
}
</script>
