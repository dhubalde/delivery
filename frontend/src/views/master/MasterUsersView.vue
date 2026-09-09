<template>
  <v-container fluid class="pa-4">
    <v-row align="center" class="mb-2">
      <v-col><h2 class="text-h6">Usuarios internos</h2></v-col>
      <v-col class="text-right"><v-btn color="primary" prepend-icon="mdi-plus" @click="dlg=true">Nuevo</v-btn></v-col>
    </v-row>
    <v-card>
      <v-list v-if="list.length" lines="two">
        <v-list-item v-for="u in list" :key="u.id" :title="`${u.username} (${u.role})`"
          :subtitle="`${(u.assigned_merchants ?? []).map(m => m.slug).join(', ') || 'sin empresas'} · ${u.is_active ? 'Activo' : 'Inactivo'}`">
          <template #append>
            <v-btn icon="mdi-cellphone-lock" variant="text" size="small" title="Sesiones" @click="openSessions(u)" />
            <v-btn icon="mdi-pencil" variant="text" size="small" @click="openEdit(u)" />
          </template>
        </v-list-item>
      </v-list>
      <v-card-text v-else class="text-medium-emphasis">Sin usuarios internos.</v-card-text>
    </v-card>
    <v-dialog v-model="dlg" max-width="520">
      <v-card>
        <v-card-title>{{ editing ? 'Editar interno' : 'Nuevo interno' }}</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.username" label="Usuario *" density="compact" :disabled="!!editing" />
          <v-text-field v-if="!editing" v-model="form.password" label="Clave *" type="password" density="compact" />
          <v-select v-model="form.role" :items="['MASTER','ADMIN','DEV','TECNICO','JUNIOR']" label="Rol *" density="compact" />
          <v-select v-model="form.assigned" :items="companyOpts" item-title="slug" item-value="id" label="Empresas asignadas" multiple chips density="compact" />
          <v-alert v-if="err" type="error" density="compact">{{ err }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dlg=false">Cancelar</v-btn>
          <v-btn color="primary" :loading="saving" @click="save">Guardar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog v-model="sessDlg" max-width="480">
      <v-card>
        <v-card-title>Sesiones de {{ sessUser?.username }}</v-card-title>
        <v-card-text>
          <v-list v-if="sessList.length" density="compact">
            <v-list-item v-for="(s, i) in sessList" :key="i"
              :title="`...${s.jti_prefix}`"
              :subtitle="`${new Date(s.created_at).toLocaleString('es-AR')} · ${s.active ? 'Activa' : 'Revocada'}`" />
          </v-list>
          <p v-else class="text-medium-emphasis">Sin sesiones.</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="error" @click="killSessions">Revocar todas</v-btn>
          <v-btn variant="text" @click="sessDlg=false">Cerrar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useMasterCompanies, useMasterUsers } from '@/composables/useMaster'
import type { InternalUser } from '@/api/panel/master.api'

const { q, createM, updateM } = useMasterUsers()
const { data: companies } = useMasterCompanies()
const list = computed(() => (q.data.value ?? []) as InternalUser[])
const companyOpts = computed(() => (companies.value ?? []).map(c => ({ id: c.id, slug: `${c.name} (${c.slug})` })))
const dlg = ref(false)
const editing = ref<number | null>(null)
const saving = ref(false)
const err = ref('')
const form = reactive({ username: '', password: '', role: 'TECNICO', assigned: [] as number[] })
function openEdit(u: InternalUser) {
  editing.value = u.id
  Object.assign(form, { username: u.username, password: '', role: u.role, assigned: (u.assigned_merchants ?? []).map(m => m.id) })
  err.value = ''; dlg.value = true
}
async function save() {
  saving.value = true; err.value = ''
  try {
    if (editing.value) await updateM.mutateAsync({ id: editing.value, role: form.role, assigned_merchants: form.assigned })
    else await createM.mutateAsync({ username: form.username, password: form.password, role: form.role, assigned_merchants: form.assigned })
    dlg.value = false; editing.value = null
    Object.assign(form, { username: '', password: '', role: 'TECNICO', assigned: [] })
  } catch (e: unknown) {
    err.value = (e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message ?? 'Error'
  } finally { saving.value = false }
}
// open create resets
import { watch } from 'vue'
import { masterApi } from '@/api/panel/master.api'
watch(dlg, (v) => { if (v && editing.value === null) Object.assign(form, { username: '', password: '', role: 'TECNICO', assigned: [] }) })
const sessDlg = ref(false)
const sessUser = ref<InternalUser | null>(null)
const sessList = ref<{ jti_prefix: string; created_at: string; active: boolean }[]>([])
async function openSessions(u: InternalUser) {
  sessUser.value = u
  sessList.value = await masterApi.sessions(u.username)
  sessDlg.value = true
}
async function killSessions() {
  if (!sessUser.value) return
  await masterApi.revokeSessions(sessUser.value.username)
  sessList.value = await masterApi.sessions(sessUser.value.username)
}
</script>
