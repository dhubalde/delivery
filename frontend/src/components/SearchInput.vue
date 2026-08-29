<template>
  <v-text-field v-model="val" density="compact" hide-details placeholder="Buscar..." prepend-inner-icon="mdi-magnify" clearable />
</template>
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
const route = useRoute()
const router = useRouter()
const val = ref((route.query.search as string) || '')
let t: ReturnType<typeof setTimeout> | null = null
watch(val, (v) => {
  if (t) clearTimeout(t)
  t = setTimeout(() => router.push({ query: { ...route.query, search: v || undefined } }), 300)
})
watch(() => route.query.search, (v) => { if (v !== val.value) val.value = (v as string) || '' })
</script>
