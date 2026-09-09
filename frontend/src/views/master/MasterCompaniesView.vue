<template>
  <v-container fluid class="pa-4">
    <v-row align="center" class="mb-2">
      <v-col><h2 class="text-h6">Empresas cliente</h2></v-col>
      <v-col class="text-right"><v-btn color="primary" prepend-icon="mdi-plus" @click="dlg=true">Onboarding</v-btn></v-col>
    </v-row>
    <v-card>
      <v-list v-if="list.length" lines="two">
        <v-list-item v-for="c in list" :key="c.id" :title="`${c.name} (${c.slug})`"
          :subtitle="`Cupo ${c.seat_limit} · ${c.has_branches ? 'Con sucursales' : 'Sin sucursales'} · ${c.is_active ? 'Activa' : 'Inactiva'}`" />
      </v-list>
      <v-card-text v-else class="text-medium-emphasis">Sin empresas.</v-card-text>
    </v-card>
    <v-dialog v-model="dlg" max-width="520">
      <v-card>
        <v-card-title>Nueva empresa</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.name" label="Nombre fantasía *" density="compact" />
          <v-text-field v-model="form.slug" label="Slug *" density="compact" hint="minúsculas-sin-espacios" />
          <v-text-field v-model="form.logo_url" label="Logo URL" density="compact" />
          <v-select v-model="form.seat_limit" :items="[10,20,30]" label="Cupo de usuarios *" density="compact" />
          <v-switch v-model="form.has_branches" label="Tiene sucursales" color="primary" />
          <v-text-field v-model="form.admin_username" label="Admin inicial *" density="compact" />
          <v-text-field v-model="form.admin_password" label="Clave inicial *" type="password" density="compact" hint="8-12, número, mayúscula y especial" />
          <v-alert v-if="err" type="error" density="compact">{{ err }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dlg=false">Cancelar</v-btn>
          <v-btn color="primary" :loading="saving" @click="save">Crear</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useMasterCompanies } from '@/composables/useMaster'
import { masterApi } from '@/api/panel/master.api'

const { data } = useMasterCompanies()
const list = computed(() => data.value ?? [])
const dlg = ref(false)
const saving = ref(false)
const err = ref('')
const form = reactive({ name: '', slug: '', logo_url: '', seat_limit: 10, has_branches: false, admin_username: '', admin_password: '' })
async function save() {
  saving.value = true; err.value = ''
  try {
    await masterApi.onboard({ ...form, logo_url: form.logo_url || undefined })
    dlg.value = false
    Object.assign(form, { name: '', slug: '', logo_url: '', seat_limit: 10, has_branches: false, admin_username: '', admin_password: '' })
  } catch (e: unknown) {
    err.value = (e as { response?: { data?: { error?: { message?: string }, slug?: string } } })?.response?.data?.error?.message
      ?? (e as { response?: { data?: { slug?: string } } })?.response?.data?.slug ?? 'Error'
  } finally { saving.value = false }
}
</script>
