<template>
  <div class="footer-contact">
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
import { useAuthStore } from '@/stores/auth.store'
import { usePublicMerchant } from '@/composables/useMerchant'

const auth = useAuthStore()
const slug = computed(() => auth.merchantSlug || 'ice-zone')
const { data: merchantData } = usePublicMerchant(slug.value) as any

const m = computed(() => (merchantData.value ?? null) as Record<string, any> | null)

const merchantName = computed(() => (m.value?.name as string) || 'Empresa — TODO merchant.name')
const phone = computed(() => (m.value?.phone as string) || (m.value?.tel as string) || 'Tel: — TODO: agregar Merchant.phone')
const email = computed(() => (m.value?.email as string) || 'Email: — TODO: agregar Merchant.email')
const address = computed(() => (m.value?.address as string) || 'Dirección: — TODO: agregar Merchant.address')
const hours = computed(() => (m.value?.hours as string) || '')
</script>
<style scoped>
.footer-contact {
  position: fixed;
  bottom: 8px;
  right: 8px;
  z-index: 1006;
  max-width: 260px;
  opacity: 0.96;
}
</style>
