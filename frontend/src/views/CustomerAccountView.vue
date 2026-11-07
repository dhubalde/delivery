<template>
  <v-container style="max-width: 560px">
    <h2 class="text-h6 mb-4">Mi cuenta</h2>
    <v-card class="pa-4 mb-4">
      <div class="text-caption text-medium-emphasis mb-1">Email (no se puede cambiar)</div>
      <div class="text-body-1 font-weight-medium mb-3">{{ customer.profile?.email || '—' }}</div>
      <v-text-field v-model="name" label="Apellido y nombre *" density="compact" :error-messages="nameErr" class="mb-2" />
      <v-text-field v-model="phone" label="Nº teléfono *" density="compact" :error-messages="phoneErr" prefix="+54" class="mb-2" type="tel" />
      <v-text-field v-model="address" label="Dirección *" density="compact" :error-messages="addressErr" hint="Calle y altura. Se usa por defecto en tus pedidos." persistent-hint class="mb-2" />
      <v-alert v-if="okMsg" type="success" variant="tonal" density="compact" class="mb-2">{{ okMsg }}</v-alert>
      <v-alert v-if="errorMsg" type="error" variant="tonal" density="compact" class="mb-2">{{ errorMsg }}</v-alert>
      <v-btn color="primary" block :loading="saving" @click="save">Guardar cambios</v-btn>
      <v-btn variant="text" block class="mt-2" @click="goCatalog">Volver al catálogo</v-btn>
    </v-card>
    <MyOrders />
  </v-container>
</template>
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { parsePhoneNumberFromString } from 'libphonenumber-js'
import { useCustomerStore } from '@/stores/customer.store'
import MyOrders from '@/components/MyOrders.vue'

const route = useRoute()
const router = useRouter()
const customer = useCustomerStore()
const slug = computed(() => (route.params.slug as string) || 'ice-zone')

const name = ref('')
const phone = ref('')
const address = ref('')
const saving = ref(false)
const okMsg = ref<string | null>(null)
const errorMsg = ref<string | null>(null)
const nameErr = ref('')
const phoneErr = ref('')
const addressErr = ref('')

function nationalWithoutTrunk(national: string): string {
  return national.replace(/^0/, '').replace(/(\s)15(\s|-)/, '$1')
}

function fillFromProfile() {
  name.value = customer.profile?.name || ''
  const raw = customer.profile?.phone || ''
  try {
    const parsed = parsePhoneNumberFromString(raw, 'AR')
    phone.value = parsed ? nationalWithoutTrunk(parsed.formatNational()) : raw.replace(/^\+54\s?9?/, '')
  } catch {
    phone.value = raw
  }
  address.value = customer.profile?.default_address || ''
}

onMounted(async () => {
  customer.hydrate(slug.value)
  if (!customer.isAuthenticated) {
    router.push(`/${slug.value}/login`)
    return
  }
  await customer.fetchMe(slug.value)
  fillFromProfile()
})
watch(() => customer.profile, fillFromProfile)

function goCatalog() {
  router.push(`/${slug.value}`)
}
async function save() {
  okMsg.value = null
  errorMsg.value = null
  nameErr.value = ''
  phoneErr.value = ''
  addressErr.value = ''
  if (!name.value.trim()) {
    nameErr.value = 'Requerido'
    return
  }
  const parsed = parsePhoneNumberFromString(phone.value.trim(), 'AR')
  if (!parsed || !parsed.isValid()) {
    phoneErr.value = 'Teléfono inválido. Sin 0 ni 15.'
    return
  }
  if (!address.value.trim() || !/\d/.test(address.value)) {
    addressErr.value = 'Incluí altura/número. Ej: San Martín 1234'
    return
  }
  saving.value = true
  try {
    await customer.updateProfile(slug.value, {
      name: name.value.trim(),
      phone: parsed.format('E.164'),
      default_address: address.value.trim(),
    })
    okMsg.value = 'Datos actualizados'
  } catch (e: unknown) {
    const resp = (e as { response?: { status?: number; data?: { error?: { message?: string } } } })?.response
    errorMsg.value = resp?.data?.error?.message || 'No se pudo guardar'
  } finally {
    saving.value = false
  }
}
</script>
