<template>
  <v-container class="fill-height d-flex align-center justify-center" fluid>
    <v-row justify="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card elevation="6" rounded="xl" class="overflow-hidden">
          <div class="login-header pa-6 text-center">
            <v-icon size="40" color="white">mdi-storefront</v-icon>
            <h1 class="text-h5 font-weight-bold mt-2" style="font-family: Comfortaa, sans-serif; color: white">Work Zone</h1>
            <p class="text-body-2 mt-1" style="color: rgba(255,255,255,0.9)">Panel de administración</p>
          </div>

          <v-card-text class="pa-6">
            <v-alert v-if="auth.isAuth" type="success" variant="tonal" class="mb-4" closable>
              Logueado como <strong>{{ auth.user?.username ?? 'usuario' }}</strong>
              <span v-if="auth.roles?.length"> — {{ auth.roles.join(', ') }}</span>
            </v-alert>

            <div v-if="auth.isAuth" class="d-flex ga-3 mb-2">
              <v-btn color="primary" block prepend-icon="mdi-view-dashboard" @click="goPanel">Ir al panel</v-btn>
            </div>
            <div v-if="auth.isAuth" class="d-flex ga-3 mb-4">
              <v-btn variant="outlined" block prepend-icon="mdi-logout" @click="logout">Logout</v-btn>
            </div>
            <v-divider v-if="auth.isAuth" class="my-4" />

            <v-form ref="formRef" @submit.prevent="onLogin">
              <v-text-field
                v-model="username"
                label="Usuario"
                prepend-inner-icon="mdi-account"
                :error-messages="usernameError"
                :disabled="loading"
                variant="outlined"
                density="comfortable"
                autocomplete="username"
                @update:model-value="usernameError = ''"
              />
              <v-text-field
                v-model="password"
                label="Contraseña"
                prepend-inner-icon="mdi-lock"
                :append-inner-icon="showPass ? 'mdi-eye-off' : 'mdi-eye'"
                :type="showPass ? 'text' : 'password'"
                :error-messages="passwordError"
                :disabled="loading"
                variant="outlined"
                density="comfortable"
                autocomplete="current-password"
                @click:append-inner="showPass = !showPass"
                @update:model-value="passwordError = ''"
              />

              <v-alert v-if="errorMsg" type="error" variant="tonal" density="compact" class="mb-3">{{ errorMsg }}</v-alert>
              <v-alert v-if="warningMsg" type="warning" variant="tonal" density="compact" class="mb-3">{{ warningMsg }}</v-alert>

              <v-btn type="submit" color="primary" block size="large" :loading="loading" prepend-icon="mdi-login" class="mb-3">
                Ingresar
              </v-btn>
            </v-form>

            <p class="text-caption text-center text-medium-emphasis mt-4">El acceso lo crea el ADMIN de tu empresa o el equipo Work Zone.</p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'
import { api } from '@/api/client'

const auth = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const usernameError = ref('')
const passwordError = ref('')
const errorMsg = ref('')
const warningMsg = ref('')
const loading = ref(false)
const showPass = ref(false)

function validate(): boolean {
  let ok = true
  usernameError.value = ''
  passwordError.value = ''
  if (!username.value.trim()) {
    usernameError.value = 'Ingresá tu usuario'
    ok = false
  }
  if (!password.value) {
    passwordError.value = 'Ingresá tu contraseña'
    ok = false
  }
  return ok
}

async function onLogin() {
  errorMsg.value = ''
  warningMsg.value = ''
  if (!validate()) return
  loading.value = true
  try {
    const res = await api.post('/auth/token/', { username: username.value, password: password.value })
    const access = res.data?.access ?? ''
    const refresh = res.data?.refresh ?? access
    const user = res.data?.user
    if (!access || !user) {
      errorMsg.value = 'Respuesta inesperada del servidor'
      return
    }
    auth.setTokens(access, refresh)
    auth.setUser(user)
    if (user.must_change_password) {
      router.push('/change-password')
      return
    }
    router.push('/panel/board')
  } catch (e: unknown) {
    const err = e as { response?: { status?: number; data?: { detail?: string; password?: string } } }
    const status = err.response?.status
    if (status === 401) {
      errorMsg.value = err.response?.data?.password ?? 'Credenciales inválidas'
    } else if (!err.response) {
      warningMsg.value = 'No se pudo conectar al backend.'
    } else {
      errorMsg.value = 'No se pudo ingresar'
    }
  } finally {
    loading.value = false
  }
}

function goPanel() {
  router.push('/panel/categories')
}

function logout() {
  auth.clear()
}
</script>

<style scoped>
.login-header {
  background: linear-gradient(135deg, #06B6D4 0%, #0891B2 100%);
}
</style>
