<template>
  <v-app>
    <v-app-bar density="compact" color="primary">
      <template #title>
        <div class="d-flex align-center ga-2">
          <AppLogo :size="130" variant="auto" />
          <span v-if="merchantName" class="text-subtitle-2 ml-2" style="opacity:0.9">{{ merchantName }}</span>
        </div>
      </template>
      <v-app-bar-nav-icon v-if="xs" @click="drawer=!drawer" />
      <v-btn v-if="customer.isAuthenticated" variant="text" size="small" @click="goAccount">{{ customer.displayName || 'Mi cuenta' }}</v-btn>
      <v-btn v-else variant="text" size="small" @click="goLogin">Ingresar</v-btn>
      <v-btn v-if="customer.isAuthenticated" variant="text" size="small" @click="onLogout">Salir</v-btn>
      <NotificationBell recipient-type="CUSTOMER" />
      <v-btn icon="mdi-brightness-6" @click="ui.toggleTheme()" />
    </v-app-bar>
    <v-navigation-drawer v-if="xs" v-model="drawer" temporary width="260">
      <SearchInput class="ma-2" />
      <CategoryNav />
      <CartDrawer class="ma-2" />
    </v-navigation-drawer>
    <v-main><v-container fluid>
      <ClosedBanner />
      <v-alert v-if="operator.active" type="info" density="compact" class="mb-2">
        <v-icon icon="mdi-phone-incoming" start />INGRESO MANUAL — cargando un pedido telefónico. Al confirmar volvés al tablero.
        <v-btn variant="text" size="x-small" class="ml-2" @click="operator.exit(); router.push('/panel/board')">Cancelar modo manual</v-btn>
      </v-alert>
      <v-row>
        <v-col v-if="!xs" cols="2"><SearchInput class="mb-3" /><CategoryNav /></v-col>
        <v-col :cols="xs?12:7"><router-view /></v-col>
        <v-col v-if="!xs" cols="3" style="max-width: 320px !important; flex: 0 0 320px !important; min-width: 320px !important"><CartDrawer :slug="slug" /><FooterContact v-if="!isContact" class="inside-cart mt-4" /></v-col>
      </v-row>
    </v-container></v-main>
    <v-banner v-if="ui.offline" color="warning" sticky>Sin conexión — datos pueden estar desactualizados</v-banner>
    <FooterContact v-if="xs || isContact" />
  </v-app>
</template>
<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useDisplay, useTheme } from 'vuetify'
import { useRoute, useRouter } from 'vue-router'
import { useUiStore } from '@/stores/ui.store'
import { useOperatorStore } from '@/stores/operator.store'
import { useOffline } from '@/composables/useOffline'
import { useCatalog } from '@/composables/useCatalog'
import { useCartStore } from '@/stores/cart.store'
import { useCustomerStore } from '@/stores/customer.store'
import CategoryNav from '@/components/CategoryNav.vue'
import SearchInput from '@/components/SearchInput.vue'
import CartDrawer from '@/components/CartDrawer.vue'
import ClosedBanner from '@/components/ClosedBanner.vue'
import AppLogo from '@/components/AppLogo.vue'
import FooterContact from '@/components/FooterContact.vue'
import NotificationBell from '@/components/NotificationBell.vue'
const ui = useUiStore()
const operator = useOperatorStore()
operator.hydrate()
const theme = useTheme()
watch(() => ui.theme, (v) => { theme.global.name.value = v }, { immediate: true })
useOffline()
const { xs } = useDisplay()
const route = useRoute()
const router = useRouter()
const isContact = computed(() => route.path.includes('/contact'))
const drawer = ref(false)
const slug = computed(() => (route.params.slug as string) || 'ice-zone')
const cart = useCartStore()
const customer = useCustomerStore()
watch(() => route.query.manual, (v) => { if (v === '1') operator.enter() }, { immediate: true })
watch(
  slug,
  (s) => {
    cart.setSlug(s)
    customer.hydrate(s)
  },
  { immediate: true },
)
const { data: aggregate } = useCatalog(slug) as any
const merchantName = computed(() => {
  const agg: any = aggregate?.value
  return agg?.merchant?.name || ''
})
function onLogout() {
  customer.logout(slug.value)
}
function goLogin() {
  router.push(`/${slug.value}/login`)
}
function goAccount() {
  router.push(`/${slug.value}/account`)
}
</script>
