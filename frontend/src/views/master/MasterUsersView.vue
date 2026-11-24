<template>
  <v-container fluid class="pa-4">
    <PageHeader title="Usuarios internos" subtitle="Equipo de plataforma y empresas asignadas">
      <v-btn color="primary" density="compact" prepend-icon="mdi-plus" @click="dlg=true">Nuevo</v-btn>
    </PageHeader>
    <DataTableCard
      v-model:search="search"
      :headers="headers"
      :items="list"
      :total="list.length"
      :search-keys="['username', 'role']"
      search-label="Buscar usuario o rol"
      :loading="loading"
      no-data-text="Sin usuarios internos."
    >
      <template #item.username="{ item }">
        <span class="font-weight-medium">{{ item.username }}</span>
      </template>
      <template #item.role="{ item }">
        <v-chip size="small" variant="tonal">{{ item.role }}</v-chip>
      </template>
      <template #item.assigned_merchants="{ item }">
        <span class="text-caption text-medium-emphasis">
          {{ merchantSlugs(item as unknown as InternalUser) }}
        </span>
      </template>
      <template #item.is_active="{ item }">
        <StatusChip :value="Boolean(item.is_active)" positive="Activo" negative="Inactivo" />
      </template>
      <template #item.actions="{ item }">
        <v-btn icon="mdi-cellphone-lock" variant="text" size="small" color="primary" title="Sesiones" @click="openSessions(item as unknown as InternalUser)" />
        <v-btn icon="mdi-pencil" variant="text" size="small" color="primary" title="Editar" @click="openEdit(item as unknown as InternalUser)" />
      </template>
    </DataTableCard>
    <FormDialog
      v-model="dlg"
      :title="editing ? 'Editar interno' : 'Nuevo interno'"
      :loading="saving"
      @submit="save"
    >
      <v-text-field v-model="form.username" label="Usuario *" density="compact" :disabled="!!editing" />
      <v-text-field v-if="!editing" v-model="form.password" label="Clave *" :type="showPass ? 'text' : 'password'"
        :append-inner-icon="showPass ? 'mdi-eye-off' : 'mdi-eye'" density="compact"
        hint="8-12 caracteres, número, mayúscula y especial"
        @click:append-inner="showPass = !showPass" />
      <v-select v-model="form.role" :items="['MASTER','ADMIN','DEV','TECNICO','JUNIOR']" label="Rol *" density="compact" />
      <v-select v-model="form.assigned" :items="companyOpts" item-title="slug" item-value="id" label="Empresas asignadas" multiple chips density="compact" />
      <v-alert v-if="err" type="error" density="compact">{{ err }}</v-alert>
    </FormDialog>

    <FormDialog
      v-model="sessDlg"
      :title="`Sesiones de ${sessUser?.username ?? ''}`"
      :max-width="480"
      hide-submit
      cancel-label="Cerrar"
    >
      <v-table v-if="sessList.length" density="compact" hover>
        <thead>
          <tr><th>Token</th><th>Inicio</th><th>Estado</th></tr>
        </thead>
        <tbody>
          <tr v-for="(s, i) in sessList" :key="i">
            <td class="text-caption">...{{ s.jti_prefix }}</td>
            <td class="text-caption">{{ new Date(s.created_at).toLocaleString('es-AR') }}</td>
            <td>
              <StatusChip :value="Boolean(s.active)" positive="Activa" negative="Revocada" />
            </td>
          </tr>
        </tbody>
      </v-table>
      <p v-else class="text-medium-emphasis">Sin sesiones.</p>
      <template #actions>
        <v-btn color="error" density="compact" @click="killSessions">Revocar todas</v-btn>
      </template>
    </FormDialog>
  </v-container>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useMasterCompanies, useMasterUsers } from '@/composables/useMaster'
import type { InternalUser } from '@/api/panel/master.api'
import { DataTableCard, FormDialog, PageHeader, StatusChip } from '@/design'

const { q, createM, updateM } = useMasterUsers()
const { data: companies } = useMasterCompanies()
const list = computed(() => (q.data.value ?? []) as InternalUser[])
const loading = computed(() => q.isLoading.value)
const search = ref('')
const headers = [
  { title: 'Usuario', key: 'username' },
  { title: 'Rol', key: 'role', align: 'center' as const },
  { title: 'Empresas', key: 'assigned_merchants' },
  { title: 'Estado', key: 'is_active', align: 'center' as const },
  { title: '', key: 'actions', sortable: false, align: 'end' as const },
]
function merchantSlugs(u: InternalUser): string {
  return (u.assigned_merchants ?? []).map((m) => m.slug).join(', ') || 'sin empresas'
}
const companyOpts = computed(() => (companies.value ?? []).map(c => ({ id: c.id, slug: `${c.name} (${c.slug})` })))
const dlg = ref(false)
const editing = ref<number | null>(null)
const saving = ref(false)
const err = ref('')
const showPass = ref(false)
const form = reactive({ username: '', password: '', role: 'TECNICO', assigned: [] as number[] })
function apiErrText(e: unknown): string {
  const d = (e as { response?: { data?: unknown } })?.response?.data as Record<string, unknown> | undefined
  if (!d || typeof d !== 'object') return 'Error de red o servidor'
  const parts: string[] = []
  for (const [k, v] of Object.entries(d)) {
    const msg = Array.isArray(v) ? v.join(' ') : typeof v === 'object' ? JSON.stringify(v) : String(v)
    parts.push(`${k}: ${msg}`)
  }
  return parts.join(' · ') || 'Error'
}
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
    err.value = apiErrText(e)
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
