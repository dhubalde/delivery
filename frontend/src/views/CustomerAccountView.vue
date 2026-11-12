<template>
  <v-container style="max-width: 560px">
    <h2 class="text-h6 mb-4">Mi cuenta</h2>
    <v-card class="pa-4 mb-4">
      <div class="text-caption text-medium-emphasis mb-1">Email (no se puede cambiar)</div>
      <div class="text-body-1 font-weight-medium mb-3">{{ customer.profile?.email || '—' }}</div>
      <div class="text-caption text-medium-emphasis mb-1">Apellido y nombre (no se puede cambiar)</div>
      <div class="text-body-1 font-weight-medium mb-3">{{ customer.profile?.name || '—' }}</div>
      <v-text-field v-model="phone" label="Nº teléfono *" density="compact" :error-messages="phoneErr" prefix="+54" class="mb-2" type="tel" />
      <v-text-field v-model="address" label="Dirección *" density="compact" :error-messages="addressErr" hint="Calle y altura. Se usa por defecto en tus pedidos." persistent-hint class="mb-2" />
      <v-alert v-if="okMsg" type="success" variant="tonal" density="compact" class="mb-2">{{ okMsg }}</v-alert>
      <v-alert v-if="errorMsg" type="error" variant="tonal" density="compact" class="mb-2">{{ errorMsg }}</v-alert>
      <v-btn color="primary" block :loading="saving" @click="askConfirm">Guardar cambios</v-btn>
      <v-btn variant="text" block class="mt-2" @click="goCatalog">Volver al catálogo</v-btn>
    </v-card>
    <v-dialog v-model="confirmDlg" max-width="440">
      <v-card>
        <v-card-title>Confirmar cambios</v-card-title>
        <v-card-text>
          <div class="text-body-2 mb-2">Se van a registrar en tu cuenta:</div>
          <div class="text-body-2">Teléfono: <strong>{{ phone }}</strong></div>
          <div class="text-body-2">Dirección: <strong>{{ address }}</strong></div>
          <div class="text-caption text-medium-emphasis mt-2">
            Quedan guardados y se usarán por defecto en tus próximos pedidos.
          </div>
          <v-alert v-if="errorMsg" type="error" variant="tonal" density="compact" class="mt-2">{{ errorMsg }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmDlg = false">Cancelar</v-btn>
          <v-btn color="primary" :loading="saving" @click="save">Confirmar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
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

const phone = ref('')
const address = ref('')
const saving = ref(false)
const okMsg = ref<string | null>(null)
const errorMsg = ref<string | null>(null)
const confirmDlg = ref(false)
const phoneErr = ref('')
const addressErr = ref('')

function nationalWithoutTrunk(national: string): string {
  return national.replace(/^0/, '').replace(/(\s)15(\s|-)/, '$1')
}

function fillFromProfile() {
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
function askConfirm() {
  okMsg.value = null
  errorMsg.value = null
  phoneErr.value = ''
  addressErr.value = ''
  const parsed = parsePhoneNumberFromString(phone.value.trim(), 'AR')
  if (!parsed || !parsed.isValid()) {
    phoneErr.value = 'Teléfono inválido. Sin 0 ni 15.'
    return
  }
  if (!address.value.trim() || !/\d/.test(address.value)) {
    addressErr.value = 'Incluí altura/número. Ej: San Martín 1234'
    return
  }
  confirmDlg.value = true
}

async function save() {
  errorMsg.value = null
  saving.value = true
  try {
    // Name and email are identity fields: they keep their registered value.
    await customer.updateProfile(slug.value, {
      name: customer.profile?.name || '',
      phone: parsePhoneNumberFromString(phone.value.trim(), 'AR')!.format('E.164'),
      default_address: address.value.trim(),
    })
    confirmDlg.value = false
    okMsg.value = 'Datos actualizados'
  } catch (e: unknown) {
    const resp = (e as { response?: { status?: number; data?: { error?: { message?: string } } } })?.response
    errorMsg.value = resp?.data?.error?.message || 'No se pudo guardar'
  } finally {
    saving.value = false
  }
}
</script>
