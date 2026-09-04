<template>
  <v-app>
    <v-navigation-drawer permanent width="240">
      <v-list density="compact" nav>
        <v-list-item subtitle="Panel" title="" />
        <v-divider />
        <v-list-item to="/panel/board" title="Kanban" prepend-icon="mdi-view-columns" />
        <v-list-item to="/panel/categories" title="Categorías" prepend-icon="mdi-shape" />
        <v-list-item to="/panel/products" title="Productos" prepend-icon="mdi-food-fork-drink" />
        <v-list-item to="/panel/flavors" title="Sabores" prepend-icon="mdi-star" />
        <v-list-item to="/panel/schedules" title="Horarios" prepend-icon="mdi-clock-outline" />
        <v-list-item to="/panel/delivery" title="Delivery" prepend-icon="mdi-moped" />
        <v-list-item to="/panel/employees" title="Empleados" prepend-icon="mdi-account-group" />
        <v-list-item to="/panel/cash-close" title="Cierre de caja" prepend-icon="mdi-cash-register" />
        <v-list-item to="/panel/merchant" title="Empresa / Logo" prepend-icon="mdi-storefront" />
        <v-divider class="my-2" />
        <v-list-item title="Reportes" prepend-icon="mdi-chart-bar" @click="showReportsDialog = true" />
        <v-list-item to="/panel/contact" title="Contacto" prepend-icon="mdi-contacts" />
      </v-list>
    </v-navigation-drawer>
    <v-app-bar density="compact" color="primary">
      <template #title><AppLogo :size="120" variant="auto" /></template>
      <v-spacer />
      <NotificationBell recipient-type="EMPLOYEE" />
      <v-btn icon="mdi-brightness-6" @click="ui.toggleTheme()" />
    </v-app-bar>
    <v-banner v-if="ui.offline" color="warning" icon="mdi-wifi-off" class="text-caption">Sin conexión — modo offline</v-banner>
    <v-main>
      <v-container>
        <router-view />
      </v-container>
    </v-main>
    <v-snackbar v-model="toast.show" :color="toast.type === 'error' ? 'error' : 'warning'" timeout="3000">{{ toast.msg }}</v-snackbar>
    <FooterContact v-if="!route.path.includes('/panel/')" />
    <v-dialog v-model="showReportsDialog" max-width="360">
      <v-card>
        <v-card-title>Reportes — clave requerida</v-card-title>
        <v-card-text>
          <v-text-field v-model="reportKey" :type="showPassword ? 'text' : 'password'" :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'" label="Clave" density="compact" hide-details autofocus @keydown.enter="submitReportsKey" @click:append-inner="showPassword = !showPassword" />
          <v-alert v-if="reportError" type="error" density="compact" class="mt-3">{{ reportError }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showReportsDialog = false">Cancelar</v-btn>
          <v-btn color="primary" @click="submitReportsKey">Entrar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>
<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { useUiStore } from '@/stores/ui.store'
import { useOffline } from '@/composables/useOffline'
import AppLogo from '@/components/AppLogo.vue'
import FooterContact from '@/components/FooterContact.vue'
import NotificationBell from '@/components/NotificationBell.vue'
const ui = useUiStore()
const theme = useTheme()
const router = useRouter()
const route = useRoute()
watch(() => ui.theme, (v) => { theme.global.name.value = v }, { immediate: true })
useOffline()
const toast = reactive({ show: false, msg: '', type: 'error' as string })
function onToast(e: Event) { const d = (e as CustomEvent).detail; toast.msg = d.msg; toast.type = d.type; toast.show = true }
onMounted(() => window.addEventListener('app:toast', onToast as EventListener))
onUnmounted(() => window.removeEventListener('app:toast', onToast as EventListener))
const showReportsDialog = ref(false)
const reportKey = ref('')
const reportError = ref('')
const showPassword = ref(false)
function submitReportsKey() {
  const expected = (import.meta.env.VITE_DASHBOARD_KEY as string | undefined) || 'dueño123'
  if (reportKey.value === expected) {
    reportError.value = ''
    showReportsDialog.value = false
    reportKey.value = ''
    router.push('/panel/dashboard')
  } else {
    reportError.value = 'Clave incorrecta'
  }
}
watch(showReportsDialog, (v) => { if (!v) { reportError.value = ''; reportKey.value = '' } })
</script>
