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
    <v-app-bar density="compact" title="Panel Ice Zone">
      <v-btn icon="mdi-brightness-6" @click="ui.toggleTheme()" />
    </v-app-bar>
    <v-main><v-container><router-view /></v-container></v-main>
  </v-app>
</template>
<script setup lang="ts">
import { useUiStore } from '@/stores/ui.store'
const ui = useUiStore()
</script>
