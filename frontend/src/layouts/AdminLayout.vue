<template>
  <v-app>
    <v-navigation-drawer permanent width="240">
      <v-list density="compact" nav>
        <v-list-item title="Ice Zone" subtitle="Panel" />
        <v-divider />
        <v-list-item to="/panel/board" title="Kanban" prepend-icon="mdi-view-columns" />
        <v-list-item to="/panel/categories" title="Categorías" prepend-icon="mdi-shape" />
        <v-list-item to="/panel/products" title="Productos" prepend-icon="mdi-ice-cream" />
        <v-list-item to="/panel/flavors" title="Sabores" prepend-icon="mdi-star" />
        <v-list-item to="/panel/schedules" title="Horarios" prepend-icon="mdi-clock-outline" />
        <v-list-item to="/panel/delivery" title="Delivery" prepend-icon="mdi-moped" />
        <v-list-item to="/panel/employees" title="Empleados" prepend-icon="mdi-account-group" />
        <v-list-item to="/panel/cash-close" title="Cierre de caja" prepend-icon="mdi-cash-register" />
      </v-list>
    </v-navigation-drawer>
    <v-app-bar density="compact" title="Panel Ice Zone" color="primary">
      <v-btn icon="mdi-brightness-6" @click="ui.toggleTheme()" />
    </v-app-bar>
    <v-banner v-if="ui.offline" color="warning" icon="mdi-wifi-off" class="text-caption">Sin conexión — modo offline</v-banner>
    <v-main>
      <v-container>
        <WeatherWidget />
        <router-view />
      </v-container>
    </v-main>
    <v-snackbar v-model="toast.show" :color="toast.type === 'error' ? 'error' : 'warning'" timeout="3000">{{ toast.msg }}</v-snackbar>
  </v-app>
</template>
<script setup lang="ts">
import { onMounted, onUnmounted, reactive, watch } from 'vue'
import { useTheme } from 'vuetify'
import { useUiStore } from '@/stores/ui.store'
import { useOffline } from '@/composables/useOffline'
import WeatherWidget from '@/components/WeatherWidget.vue'
const ui = useUiStore()
const theme = useTheme()
watch(() => ui.theme, (v) => { theme.global.name.value = v }, { immediate: true })
useOffline()
const toast = reactive({ show: false, msg: '', type: 'error' as string })
function onToast(e: Event) { const d = (e as CustomEvent).detail; toast.msg = d.msg; toast.type = d.type; toast.show = true }
onMounted(() => window.addEventListener('app:toast', onToast as EventListener))
onUnmounted(() => window.removeEventListener('app:toast', onToast as EventListener))
</script>
