<template>
  <v-container class="pa-6" style="max-width: 480px">
    <h2 class="text-h6 mb-1">Cambiar clave</h2>
    <p class="text-body-2 text-medium-emphasis mb-4">Tu clave es inicial o venció. Definí una nueva para seguir.</p>
    <v-text-field v-model="current" label="Clave actual *" type="password" density="compact" />
    <v-text-field v-model="next" label="Nueva clave *" type="password" density="compact" hint="8-12 caracteres, número, mayúscula y especial" />
    <v-alert v-if="err" type="error" density="compact" class="mb-2">{{ err }}</v-alert>
    <v-btn color="primary" block :loading="saving" @click="save">Guardar y entrar</v-btn>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { usersApi } from '@/api/panel/users.api'
import { useAuthStore } from '@/stores/auth.store'

const router = useRouter()
const auth = useAuthStore()
const current = ref('')
const next = ref('')
const err = ref('')
const saving = ref(false)
async function save() {
  saving.value = true; err.value = ''
  try {
    await usersApi.changePassword({ current_password: current.value, new_password: next.value })
    auth.setMustChange(false)
    router.replace('/panel')
  } catch (e: unknown) {
    err.value = (e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message ?? 'Error'
  } finally { saving.value = false }
}
</script>
