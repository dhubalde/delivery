<template>
  <v-app>
    <v-navigation-drawer permanent width="240">
      <v-list density="compact" nav>
        <v-list-item title="Ice Zone" subtitle="Panel" />
        <v-divider />
        <v-list-item to="/panel/board" title="Kanban" prepend-icon="mdi-view-columns" />
        <v-list-item to="/panel/catalog" title="Catálogo" prepend-icon="mdi-ice-cream" />
        <v-list-item to="/panel/ops" title="Operaciones" prepend-icon="mdi-cog" />
      </v-list>
    </v-navigation-drawer>
    <v-app-bar density="compact" title="Panel Ice Zone" color="primary">
      <v-btn icon="mdi-brightness-6" @click="ui.toggleTheme()" />
    </v-app-bar>
    <v-main><v-container><router-view /></v-container></v-main>
  </v-app>
</template>
<script setup lang="ts">
import { watch } from 'vue'
import { useTheme } from 'vuetify'
import { useUiStore } from '@/stores/ui.store'
const ui = useUiStore()
const theme = useTheme()
watch(() => ui.theme, (v) => { theme.global.name.value = v }, { immediate: true })
</script>
