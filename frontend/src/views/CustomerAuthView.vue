<template>
  <v-container style="max-width: 480px">
    <h2 class="text-h6 mb-4">Mi cuenta</h2>
    <v-tabs v-model="tab" class="mb-4">
      <v-tab value="login">Ingresar</v-tab>
      <v-tab value="register">Registrarme</v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item value="login">
        <v-form @submit.prevent="doLogin">
          <v-text-field v-model="email" label="Email *" type="email" density="compact" :error-messages="emailErr" class="mb-2" />
          <v-text-field v-model="password" label="Contraseña *" :type="showPass ? 'text' : 'password'" :append-inner-icon="showPass ? 'mdi-eye-off' : 'mdi-eye'" density="compact" :error-messages="passErr" class="mb-2" @click:append-inner="showPass = !showPass" />
          <v-alert v-if="errorMsg" type="error" variant="tonal" density="compact" class="mb-2">{{ errorMsg }}</v-alert>
          <v-btn type="submit" color="primary" block :loading="loading">Ingresar</v-btn>
        </v-form>
      </v-window-item>
      <v-window-item value="register">
        <v-form @submit.prevent="doRegister">
          <v-text-field v-model="name" label="Apellido y nombre *" density="compact" :error-messages="fieldErr('name')" class="mb-2" />
          <v-text-field v-model="email" label="Email *" type="email" density="compact" :error-messages="fieldErr('email')" class="mb-2" />
          <v-text-field v-model="phone" label="Nº teléfono *" density="compact" :error-messages="fieldErr('phone')" prefix="+54" class="mb-2" type="tel" />
          <v-text-field v-model="address" label="Dirección *" density="compact" :error-messages="fieldErr('address')" hint="Calle y altura. Ej: San Martín 1234" persistent-hint class="mb-2" />
          <v-text-field v-model="password" label="Contraseña * (mín. 6)" :type="showPass ? 'text' : 'password'" :append-inner-icon="showPass ? 'mdi-eye-off' : 'mdi-eye'" density="compact" :error-messages="fieldErr('password')" class="mb-2" @click:append-inner="showPass = !showPass" />
          <v-alert v-if="errorMsg" type="error" variant="tonal" density="compact" class="mb-2">{{ errorMsg }}</v-alert>
          <v-btn type="submit" color="primary" block :loading="loading">Crear cuenta</v-btn>
        </v-form>
      </v-window-item>
    </v-window>
  </v-container>
</template>
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { parsePhoneNumberFromString } from 'libphonenumber-js'
import { useCustomerStore } from '@/stores/customer.store'

const route = useRoute()
const router = useRouter()
const customer = useCustomerStore()
const slug = computed(() => (route.params.slug as string) || 'ice-zone')

const tab = ref('login')
const email = ref('')
const phone = ref('')
const name = ref('')
const address = ref('')
const password = ref('')
const loading = ref(false)
const showPass = ref(false)
const errorMsg = ref<string | null>(null)
const details = ref<Record<string, string>>({})
const emailErr = ref('')
const passErr = ref('')

function fieldErr(k: string): string {
  return details.value[k] ?? ''
}

function validEmail(v: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim())
}

async function doLogin() {
  errorMsg.value = null
  emailErr.value = ''
  passErr.value = ''
  if (!validEmail(email.value)) {
    emailErr.value = 'Email inválido'
    return
  }
  if (!password.value) {
    passErr.value = 'Ingresá tu contraseña'
    return
  }
  loading.value = true
  try {
    await customer.login(slug.value, { email: email.value.trim().toLowerCase(), password: password.value })
    router.push(`/${slug.value}/account`)
  } catch (e: unknown) {
    const status = (e as { response?: { status?: number } })?.response?.status
    errorMsg.value = status === 401 ? 'Email o contraseña inválidos' : 'No se pudo ingresar'
  } finally {
    loading.value = false
  }
}

async function doRegister() {
  errorMsg.value = null
  details.value = {}
  let bad = false
  if (!name.value.trim()) {
    details.value.name = 'Requerido'
    bad = true
  }
  if (!validEmail(email.value)) {
    details.value.email = 'Email inválido'
    bad = true
  }
  const parsed = parsePhoneNumberFromString(phone.value.trim(), 'AR')
  if (!parsed || !parsed.isValid()) {
    details.value.phone = 'Teléfono inválido. Sin 0 ni 15.'
    bad = true
  }
  if (!address.value.trim() || !/\d/.test(address.value)) {
    details.value.address = 'Incluí altura/número. Ej: San Martín 1234'
    bad = true
  }
  if (password.value.length < 6) {
    details.value.password = 'Mínimo 6 caracteres'
    bad = true
  }
  if (bad) return
  loading.value = true
  try {
    await customer.register(slug.value, {
      email: email.value.trim().toLowerCase(),
      phone: parsed!.format('E.164'),
      name: name.value.trim(),
      address: address.value.trim(),
      password: password.value,
    })
    router.push(`/${slug.value}/account`)
  } catch (e: unknown) {
    const resp = (e as { response?: { status?: number; data?: { error?: { message?: string } } } })?.response
    errorMsg.value = resp?.data?.error?.message || (resp?.status === 409 ? 'Ese mail ya está registrado' : 'No se pudo crear la cuenta')
  } finally {
    loading.value = false
  }
}
</script>
