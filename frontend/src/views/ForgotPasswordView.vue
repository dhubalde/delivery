<template>
  <v-container class="fill-height d-flex align-center justify-center" fluid>
    <v-row justify="center">
      <v-col cols="12" sm="8" md="6" lg="5">
        <v-card elevation="6" rounded="xl" class="overflow-hidden">
          <div class="login-header pa-6 text-center">
            <v-icon size="40" color="white">mdi-lock-reset</v-icon>
            <h1 class="text-h5 font-weight-bold mt-2" style="font-family: Comfortaa, sans-serif; color: white">Recuperar contraseña</h1>
            <p class="text-body-2 mt-1" style="color: rgba(255,255,255,0.9)">Ingresá tu usuario para generar un token (20 min, un solo uso)</p>
          </div>

          <v-card-text class="pa-6">
            <!-- Step 1: generate token -->
            <h3 class="text-subtitle-1 font-weight-bold mb-2">Paso 1 — Generar token</h3>
            <v-text-field
              v-model="username"
              label="Usuario"
              prepend-inner-icon="mdi-account"
              variant="outlined"
              density="comfortable"
              :disabled="loadingToken"
              autocomplete="username"
              @update:model-value="errorStep1 = ''"
            />
            <v-btn color="primary" block :loading="loadingToken" prepend-icon="mdi-key-plus" class="mb-3" @click="onGenerateToken">
              Generar token
            </v-btn>

            <v-alert v-if="errorStep1" type="error" variant="tonal" density="compact" class="mb-3">{{ errorStep1 }}</v-alert>

            <v-text-field
              v-if="resetToken"
              :model-value="resetToken"
              label="Token generado (cópialo)"
              prepend-inner-icon="mdi-key"
              variant="outlined"
              density="comfortable"
              readonly
              append-inner-icon="mdi-content-copy"
              @click:append-inner="copyToken"
            />
            <p v-if="resetToken" class="text-caption text-medium-emphasis mb-4">El token expira en 20 minutos y es de un solo uso. Pégalo abajo para cambiar tu clave.</p>

            <v-divider class="my-4" />

            <!-- Step 2: reset -->
            <h3 class="text-subtitle-1 font-weight-bold mb-2">Paso 2 — Cambiar clave</h3>
            <v-text-field
              v-model="token"
              label="Token (opcional, se genera solo si lo dejás vacío)"
              prepend-inner-icon="mdi-key-variant"
              variant="outlined"
              density="comfortable"
              :placeholder="resetToken ? 'Autocompletado — podés dejarlo vacío' : 'Se genera automático si lo dejás vacío'"
              hint="Si lo dejás vacío, se genera solo con tu usuario"
              persistent-hint
            />
            <v-text-field
              v-model="newPassword"
              label="Nueva clave"
              prepend-inner-icon="mdi-lock"
              :append-inner-icon="showPass ? 'mdi-eye-off' : 'mdi-eye'"
              :type="showPass ? 'text' : 'password'"
              variant="outlined"
              density="comfortable"
              counter
              hint="8-12 chars, número, mayúscula y especial"
              persistent-hint
              autocomplete="new-password"
              @click:append-inner="showPass = !showPass"
            />
            <v-text-field
              v-model="confirm"
              label="Confirmar clave"
              prepend-inner-icon="mdi-lock-check"
              :append-inner-icon="showPass2 ? 'mdi-eye-off' : 'mdi-eye'"
              :type="showPass2 ? 'text' : 'password'"
              variant="outlined"
              density="comfortable"
              autocomplete="new-password"
              @click:append-inner="showPass2 = !showPass2"
            />

            <v-alert v-if="errorStep2" type="error" variant="tonal" density="compact" class="mb-3">{{ errorStep2 }}</v-alert>
            <v-alert v-if="success" type="success" variant="tonal" class="mb-3">Clave cambiada, volvé a login</v-alert>

            <v-btn v-if="!success" color="primary" block size="large" :loading="loadingReset" prepend-icon="mdi-check" class="mb-3" @click="onReset">
              Cambiar clave
            </v-btn>
            <v-btn v-if="success" color="primary" block prepend-icon="mdi-login" to="/login" class="mb-3">Ir a login</v-btn>
            <v-btn variant="text" block to="/login">Volver a login</v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { api } from '@/api/client'

const username = ref('')
const resetToken = ref('')
const token = ref('')
const newPassword = ref('')
const confirm = ref('')
const errorStep1 = ref('')
const errorStep2 = ref('')
const success = ref(false)
const loadingToken = ref(false)
const loadingReset = ref(false)
const showPass = ref(false)
const showPass2 = ref(false)

watch(resetToken, (val) => {
  if (val && !token.value) token.value = val
})

async function onGenerateToken() {
  errorStep1.value = ''
  if (!username.value.trim()) {
    errorStep1.value = 'Ingresá tu usuario'
    return
  }
  loadingToken.value = true
  try {
    const res = await api.post('/v1/users/forgot-password/', { username: username.value.trim() })
    resetToken.value = res.data?.reset_token ?? ''
    if (!resetToken.value) errorStep1.value = 'No se pudo generar el token'
  } catch (e: unknown) {
    const err = e as { response?: { status?: number; data?: { error?: { message?: string }; detail?: string } } }
    const status = err.response?.status
    if (status === 404) errorStep1.value = 'Usuario no encontrado'
    else errorStep1.value = err.response?.data?.error?.message ?? err.response?.data?.detail ?? 'Error al generar token'
  } finally {
    loadingToken.value = false
  }
}

async function onReset() {
  errorStep2.value = ''
  success.value = false
  if (!newPassword.value) {
    errorStep2.value = 'Ingresá la nueva clave'
    return
  }
  if (newPassword.value !== confirm.value) {
    errorStep2.value = 'Las claves no coinciden'
    return
  }
  let effectiveToken = (token.value || resetToken.value || '').trim()
  // Si no hay token pegado, generarlo automáticamente con el username (sin que el usuario copie/pegue)
  if (!effectiveToken) {
    if (!username.value.trim()) {
      errorStep2.value = 'Ingresá tu usuario arriba y generá el token, o poné el token manualmente'
      return
    }
    try {
      const r = await api.post('/v1/users/forgot-password/', { username: username.value.trim() })
      effectiveToken = r.data?.reset_token ?? ''
      resetToken.value = effectiveToken
      token.value = effectiveToken
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { error?: { message?: string } } } }
      errorStep2.value = err.response?.status === 404 ? 'Usuario no encontrado' : (err.response?.data?.error?.message ?? 'No se pudo generar el token')
      return
    }
  }
  if (!effectiveToken) {
    errorStep2.value = 'No se pudo obtener el token'
    return
  }
  loadingReset.value = true
  try {
    await api.post('/v1/users/reset-confirm/', { token: effectiveToken, new_password: newPassword.value })
    success.value = true
    errorStep2.value = ''
  } catch (e: unknown) {
    const err = e as { response?: { status?: number; data?: { error?: { message?: unknown; code?: string } } } }
    const status = err.response?.status
    const data = err.response?.data?.error
    let msg = ''
    if (status === 410) msg = 'Token inválido o expirado'
    else if (status === 422) {
      const m = data?.message
      if (Array.isArray((m as Record<string, unknown>)?.password)) msg = ((m as Record<string, string[]>)?.password ?? []).join(' ')
      else if (typeof m === 'string') msg = m
      else if (m && typeof m === 'object') msg = JSON.stringify(m)
      else msg = 'Contraseña débil: 8-12 chars, número, mayúscula y especial'
    } else {
      const raw = data?.message
      if (typeof raw === 'string') msg = raw
      else if (raw) msg = JSON.stringify(raw)
      else msg = 'No se pudo cambiar la clave'
    }
    errorStep2.value = msg
  } finally {
    loadingReset.value = false
  }
}

async function copyToken() {
  try {
    await navigator.clipboard.writeText(resetToken.value)
  } catch {
    // fallback: select not needed, keep token visible
  }
}
</script>

<style scoped>
.login-header {
  background: linear-gradient(135deg, #06B6D4 0%, #0891B2 100%);
}
</style>
