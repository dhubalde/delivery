<template>
  <v-container fluid class="pa-4">
    <v-row align="center" class="mb-2">
      <v-col><h2 class="text-h6">Usuarios</h2></v-col>
      <v-col class="text-right">
        <v-btn color="primary" prepend-icon="mdi-plus" :disabled="!isAdmin" @click="openCreate">Nuevo</v-btn>
      </v-col>
    </v-row>
    <v-alert v-if="formError" type="error" density="compact" class="mb-2">{{ formError }}</v-alert>
    <v-card>
      <v-list v-if="list.length" lines="two">
        <v-list-item v-for="u in list" :key="u.id"
          :title="u.username"
          :subtitle="`${u.role} · ${u.kind}${u.sector ? ' · ' + u.sector : ''} · ${u.is_active ? 'Activo' : 'Inactivo'}`">
          <template #append>
            <v-btn icon="mdi-pencil" variant="text" size="small" @click="openEdit(u)" />
            <v-btn icon="mdi-key" variant="text" size="small" title="Generar reseteo" @click="openReset(u)" />
            <v-btn icon="mdi-delete" variant="text" size="small" @click="askRemove(u)" />
          </template>
        </v-list-item>
      </v-list>
      <v-card-text v-else class="text-medium-emphasis">Sin usuarios. Creá el primero con Nuevo.</v-card-text>
    </v-card>

    <v-dialog v-model="dlg" max-width="520">
      <v-card>
        <v-card-title>{{ editing ? 'Editar usuario' : 'Nuevo usuario' }}</v-card-title>
        <v-card-text>
          <v-alert v-if="form.role === 'ADMIN'" type="warning" density="compact" class="mb-3">
            El rol ADMIN administra usuarios, caja y configuración. Solo para mandos medios o quien mejor maneje el sistema.
          </v-alert>
          <v-text-field v-model="form.username" label="Usuario *" density="compact" :disabled="!!editing" :error-messages="details.username ?? ''" />
          <v-text-field v-if="!editing" v-model="form.password" label="Clave inicial *" type="password" density="compact" hint="8-12 caracteres, número, mayúscula y especial" :error-messages="details.password ?? ''" />
          <v-select v-model="form.role" :items="roleOpts" label="Rol *" density="compact" :error-messages="details.role ?? ''" />
          <v-select v-model="form.kind" :items="['PERSONAL','STATION']" label="Tipo" density="compact" />
          <v-text-field v-model="form.sector" label="Sector (solo estación)" density="compact" hint="RECIBIDO, PREPARACION, FACTURACION, LOGISTICA" />
          <v-switch v-model="form.is_active" label="Activo" color="primary" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dlg=false">Cancelar</v-btn>
          <v-btn color="primary" :loading="saving" @click="save">Guardar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="resetDlg" max-width="520">
      <v-card>
        <v-card-title>Resetear clave de {{ resetUser?.username }}</v-card-title>
        <v-card-text>
          <p class="text-body-2 mb-2">Se genera un token de un solo uso (20 min). Pasáselo por un canal seguro, nunca por chat grupal.</p>
          <v-text-field v-if="resetToken" :model-value="resetToken" label="Token" readonly density="compact" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="resetDlg=false">Cerrar</v-btn>
          <v-btn color="primary" :loading="resetting" @click="doReset">Generar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="removeDlg" max-width="420">
      <v-card>
        <v-card-title>Desactivar usuario</v-card-title>
        <v-card-text>Se desactiva <b>{{ removeTarget?.username }}</b> (libera cupo, conserva historial).</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="removeDlg=false">Cancelar</v-btn>
          <v-btn color="error" :loading="removeM.isPending.value" @click="doRemove">Desactivar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useAdminUsers, userErrDetails, type AppUser } from '@/composables/useAdminUsers'
import { usersApi, type OperativeRole, type UserKind } from '@/api/panel/users.api'
import { useAuthStore } from '@/stores/auth.store'

const auth = useAuthStore()
const isAdmin = computed(() => auth.hasAnyRole(['ADMIN']))
const { q, createM, updateM, removeM } = useAdminUsers()
const data = computed(() => q.data.value as AppUser[] | undefined)
const list = computed(() => data.value ?? [])

const roleOpts: OperativeRole[] = ['ADMIN', 'CAJERO', 'PREPARADOR', 'REPARTIDOR', 'TOMA_PEDIDOS']
const dlg = ref(false)
const editing = ref<number | null>(null)
const saving = ref(false)
const details = ref<Record<string, string>>({})
const formError = ref('')
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
