<template>
  <v-app>
    <v-app-bar title="Zona Ice" density="compact">
      <template #prepend><img src="@/assets/logo-zona-ice.svg" width="32" height="32" alt="Zona Ice" /></template>
      <v-btn icon="mdi-brightness-6" @click="ui.toggleTheme()" />
    </v-app-bar>
    <v-main><v-container><router-view /></v-container></v-main>
    <v-banner v-if="ui.offline" color="warning" sticky>Sin conexión — datos pueden estar desactualizados</v-banner>
  </v-app>
</template>
<script setup lang="ts">
import { useUiStore } from '@/stores/ui.store'
import { useOffline } from '@/composables/useOffline'
const ui = useUiStore()
useOffline()
</script>
