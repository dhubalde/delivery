<template>
  <v-app>
    <v-app-bar density="compact" color="primary">
      <template #title><AppLogo :size="130" variant="auto" /></template>
      <v-app-bar-nav-icon v-if="xs" @click="drawer=!drawer" />
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
      <v-row>
        <v-col v-if="!xs" cols="2"><SearchInput class="mb-3" /><CategoryNav /></v-col>
        <v-col :cols="xs?12:7"><router-view /></v-col>
        <v-col v-if="!xs" cols="3" style="max-width: 320px !important; flex: 0 0 320px !important; min-width: 320px !important"><CartDrawer /><FooterContact v-if="!isContact" class="inside-cart mt-4" /></v-col>
      </v-row>
    </v-container></v-main>
    <v-banner v-if="ui.offline" color="warning" sticky>Sin conexión — datos pueden estar desactualizados</v-banner>
    <FooterContact v-if="xs || isContact" />
  </v-app>
</template>
<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useDisplay, useTheme } from 'vuetify'
import { useRoute } from 'vue-router'
import { useUiStore } from '@/stores/ui.store'
import { useOffline } from '@/composables/useOffline'
import CategoryNav from '@/components/CategoryNav.vue'
import SearchInput from '@/components/SearchInput.vue'
import CartDrawer from '@/components/CartDrawer.vue'
import ClosedBanner from '@/components/ClosedBanner.vue'
import AppLogo from '@/components/AppLogo.vue'
import FooterContact from '@/components/FooterContact.vue'
import NotificationBell from '@/components/NotificationBell.vue'
const ui = useUiStore()
const theme = useTheme()
watch(() => ui.theme, (v) => { theme.global.name.value = v }, { immediate: true })
useOffline()
const { xs } = useDisplay()
const route = useRoute()
const isContact = computed(() => route.path.includes('/contact'))
const drawer = ref(false)
</script>
