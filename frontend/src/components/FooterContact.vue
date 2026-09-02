<template>
  <div v-if="!isContact" class="footer-contact">
    <v-card density="compact" variant="tonal" rounded="lg" elevation="2" class="pa-2">
      <div class="text-caption font-weight-medium d-flex align-center ga-1">
        <v-icon size="14">mdi-storefront</v-icon>
        <span>{{ merchantName }}</span>
      </div>
      <div class="text-caption d-flex align-center ga-1">
        <v-icon size="12">mdi-phone</v-icon>
        <span>{{ phone }}</span>
      </div>
      <div class="text-caption d-flex align-center ga-1">
        <v-icon size="12">mdi-email-outline</v-icon>
        <span>{{ email }}</span>
      </div>
      <div class="text-caption d-flex align-center ga-1">
        <v-icon size="12">mdi-map-marker-outline</v-icon>
        <span>{{ address }}</span>
      </div>
      <div v-if="hours" class="text-caption d-flex align-center ga-1">
        <v-icon size="12">mdi-clock-outline</v-icon>
        <span>{{ hours }}</span>
      </div>
    </v-card>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'
import { usePublicMerchant } from '@/composables/useMerchant'

const route = useRoute()
const isContact = computed(() => route.path.includes('/contact'))
const auth = useAuthStore()
const slug = computed(() => auth.merchantSlug || 'ice-zone')
const { data: merchantData } = usePublicMerchant(slug.value) as any

const m = computed(() => (merchantData.value ?? null) as Record<string, any> | null)

const merchantName = computed(() => (m.value?.name as string) || 'Group-q')
const phone = computed(() => (m.value?.phone as string) || (m.value?.tel as string) || '3446-200156')
const email = computed(() => (m.value?.email as string) || 'contacto@group-q.tech')
const address = computed(() => (m.value?.address as string) || 'Dirección: — TODO: agregar Merchant.address')
const hours = computed(() => (m.value?.hours as string) || '')
</script>
<style scoped>
.footer-contact {
  position: fixed;
  bottom: 12px;
  right: 16px;
  z-index: 1006;
  width: 320px;
  max-width: calc(100vw - 24px);
  opacity: 0.98;
}
@media (max-width: 960px) {
  .footer-contact {
    position: static;
    width: 100%;
    max-width: 100%;
    margin: 12px auto 0;
  }
}
</style>
