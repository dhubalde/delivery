<template>
  <v-container fluid class="pa-4">
    <PageHeader title="Usuarios" subtitle="Cuentas, roles y accesos">
      <v-btn color="primary" density="compact" prepend-icon="mdi-plus" :disabled="!isAdmin" @click="openCreate">Nuevo</v-btn>
    </PageHeader>
    <v-alert v-if="formError" type="error" density="compact" class="mb-2">{{ formError }}</v-alert>
    <DataTableCard
      v-model:search="search"
      :headers="headers"
      :items="list"
      :total="list.length"
      :search-keys="['username', 'sector']"
      search-label="Buscar usuario"
      :loading="loading"
      no-data-text="Sin usuarios. Creá el primero con Nuevo."
    >
      <template #item.username="{ item }">
        <div class="font-weight-medium">{{ item.username }}</div>
        <div class="text-caption text-medium-emphasis font-weight-regular">{{ item.sector ?? '' }}</div>
      </template>
      <template #item.role="{ item }">
        <span class="text-caption">{{ item.role }}</span>
      </template>
      <template #item.kind="{ item }">
        <span class="text-caption text-medium-emphasis">{{ item.kind }}</span>
      </template>
      <template #item.is_active="{ item }">
        <StatusChip :value="Boolean(item.is_active)" positive="Activo" negative="Inactivo" />
      </template>
      <template #item.actions="{ item }">
        <v-btn icon="mdi-pencil" variant="text" size="small" density="compact" color="primary" title="Editar" @click="openEdit(item as unknown as AppUser)" />
        <v-btn icon="mdi-key" variant="text" size="small" density="compact" color="warning" title="Generar reseteo" @click="openReset(item as unknown as AppUser)" />
        <v-btn icon="mdi-delete" variant="text" size="small" density="compact" color="error" title="Desactivar" @click="askRemove(item as unknown as AppUser)" />
      </template>
    </DataTableCard>

    <FormDialog
      v-model="dlg"
      :title="editing ? 'Editar usuario' : 'Nuevo usuario'"
      :loading="saving"
      @submit="save"
    >
      <v-alert v-if="form.role === 'ADMIN'" type="warning" density="compact" class="mb-3">
        El rol ADMIN administra usuarios, caja y configuración. Solo para mandos medios o quien mejor maneje el sistema.
      </v-alert>
      <v-text-field v-model="form.username" label="Usuario *" density="compact" :disabled="!!editing" :error-messages="details.username ?? ''" />
      <v-text-field v-if="!editing" v-model="form.password" label="Clave inicial *" :type="showPass ? 'text' : 'password'"
        :append-inner-icon="showPass ? 'mdi-eye-off' : 'mdi-eye'" density="compact"
        hint="8-12 caracteres, número, mayúscula y especial" :error-messages="details.password ?? ''"
        @click:append-inner="showPass = !showPass" />
      <v-select v-model="form.role" :items="roleOpts" label="Rol *" density="compact" :error-messages="details.role ?? ''" />
      <v-select v-model="form.kind" :items="['PERSONAL','STATION']" label="Tipo" density="compact" />
      <v-select v-model="form.sector" :items="['', 'RECIBIDO', 'PREPARACION', 'FACTURACION', 'LOGISTICA', 'TODAS']" label="Sector" density="compact" hint="Vacío = por rol. TODAS = todas las estaciones (negocio chico)" />
      <v-switch v-model="form.is_active" label="Activo" color="primary" />
    </FormDialog>

    <FormDialog
      v-model="resetDlg"
      :title="`Resetear clave de ${resetUser?.username ?? ''}`"
      hide-submit
      cancel-label="Cerrar"
    >
      <p class="text-body-2 mb-2">Se genera un token de un solo uso (20 min). Pasáselo por un canal seguro, nunca por chat grupal.</p>
      <v-text-field v-if="resetToken" :model-value="resetToken" label="Token" readonly density="compact" />
      <template #actions>
        <v-btn color="primary" density="compact" :loading="resetting" @click="doReset">Generar</v-btn>
      </template>
    </FormDialog>

    <FormDialog
      v-model="removeDlg"
      title="Desactivar usuario"
      :max-width="420"
      hide-submit
    >
      Se desactiva <b>{{ removeTarget?.username }}</b> (libera cupo, conserva historial).
      <template #actions>
        <v-btn color="error" density="compact" :loading="removeM.isPending.value" @click="doRemove">Desactivar</v-btn>
      </template>
    </FormDialog>
  </v-container>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useAdminUsers, userErrDetails, type AppUser } from '@/composables/useAdminUsers'
import { usersApi, type OperativeRole, type UserKind } from '@/api/panel/users.api'
import { useAuthStore } from '@/stores/auth.store'
import { DataTableCard, FormDialog, PageHeader, StatusChip } from '@/design'

const auth = useAuthStore()
const isAdmin = computed(() => auth.hasAnyRole(['ADMIN']))
const { q, createM, updateM, removeM } = useAdminUsers()
const data = computed(() => q.data.value as AppUser[] | undefined)
const loading = computed(() => q.isLoading.value)
const search = ref('')
// Filtering happens inside DataTableCard (search-keys), so the table owns it.
const list = computed(() => data.value ?? [])
const headers = [
  { title: 'Usuario', key: 'username' },
  { title: 'Rol', key: 'role', align: 'center' as const },
  { title: 'Tipo', key: 'kind', align: 'center' as const },
  { title: 'Estado', key: 'is_active', align: 'center' as const },
  { title: '', key: 'actions', sortable: false, align: 'end' as const },
]

const roleOpts: OperativeRole[] = ['ADMIN', 'CAJERO', 'PREPARADOR', 'REPARTIDOR', 'TOMA_PEDIDOS']
const dlg = ref(false)
const editing = ref<number | null>(null)
const saving = ref(false)
const details = ref<Record<string, string>>({})
const formError = ref('')
const showPass = ref(false)
const form = reactive({ username: '', password: '', role: 'CAJERO' as OperativeRole, kind: 'PERSONAL' as UserKind, sector: '', is_active: true })

const removeDlg = ref(false)
const removeTarget = ref<AppUser | null>(null)
const resetDlg = ref(false)
const resetUser = ref<AppUser | null>(null)
const resetToken = ref('')
const resetting = ref(false)

function openCreate() {
  editing.value = null
  Object.assign(form, { username: '', password: '', role: 'CAJERO', kind: 'PERSONAL', sector: '', is_active: true })
  details.value = {}; formError.value = ''; dlg.value = true
}
function openEdit(u: AppUser) {
  editing.value = u.id
  Object.assign(form, { username: u.username, password: '', role: u.role, kind: u.kind, sector: u.sector ?? '', is_active: u.is_active })
  details.value = {}; formError.value = ''; dlg.value = true
}
async function save() {
  if (!form.username.trim()) { details.value = { username: 'Usuario requerido' }; return }
  if (!editing.value && !form.password) { details.value = { password: 'Clave requerida' }; return }
  saving.value = true; details.value = {}; formError.value = ''
  const payload = {
    username: form.username, role: form.role, kind: form.kind,
    sector: form.sector.trim() || null, is_active: form.is_active,
    ...(editing.value ? {} : { password: form.password }),
  }
  try {
    if (editing.value) await updateM.mutateAsync({ id: editing.value, ...payload })
    else await createM.mutateAsync(payload as never)
    dlg.value = false
  } catch (e: unknown) {
    const d = userErrDetails(e)
    if (Object.keys(d).length) details.value = d
    else formError.value = (e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message ?? 'Error'
  } finally { saving.value = false }
}
function askRemove(u: AppUser) { removeTarget.value = u; removeDlg.value = true }
async function doRemove() {
  if (!removeTarget.value) return
  await removeM.mutateAsync(removeTarget.value.id)
  removeDlg.value = false
}
function openReset(u: AppUser) { resetUser.value = u; resetToken.value = ''; resetDlg.value = true }
async function doReset() {
  if (!resetUser.value) return
  resetting.value = true
  try {
    const r = await usersApi.resetRequest(resetUser.value.username)
    resetToken.value = r.reset_token
  } finally { resetting.value = false }
}
</script>
