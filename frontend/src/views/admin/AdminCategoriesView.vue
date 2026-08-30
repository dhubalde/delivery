<template>
  <v-container>
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 style="font-family:Comfortaa">Categorías</h2>
      <v-btn color="primary" :disabled="!isAdmin" @click="openCreate">Nueva</v-btn>
    </div>
    <v-alert v-if="!isAdmin" type="warning" class="mb-4">Solo ADMIN puede editar categorías</v-alert>
    <v-alert v-if="isError && isForbidden" type="error">403 — Permiso denegado (ADMIN requerido)</v-alert>
    <v-row class="mb-4">
      <v-col cols="12" md="4"><v-text-field v-model="search" label="Buscar (prefix)" clearable density="compact" /></v-col>
    </v-row>
    <v-skeleton-loader v-if="isLoading" type="list-item@3" />
    <v-alert v-else-if="!list.length" type="info">Sin categorías — creá la primera</v-alert>
    <template v-else>
      <div class="d-flex align-center flex-nowrap px-2 py-0 text-caption text-medium-emphasis" style="flex-wrap:nowrap; font-size:12px; min-height:36px; height:36px">
        <span style="flex:1; min-width:0; font-size:12px" class="text-truncate">Nombre</span>
        <span style="width:150px; flex-shrink:0; font-size:12px" class="text-right">Acciones</span>
      </div>
      <v-divider />
      <v-list density="compact" lines="one">
        <v-list-item v-for="c in list" :key="c.id" density="compact" style="min-height:36px; height:36px" class="py-0 px-2">
          <template #default>
            <div class="d-flex align-center flex-nowrap" style="flex:1; min-width:0; overflow:hidden"><span class="font-weight-medium text-truncate" style="font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis">{{ c.name }}</span><span class="ml-2 text-caption text-medium-emphasis flex-shrink-0" style="font-size:12px; white-space:nowrap">#{{ c.position }} · {{ c.is_active ? 'Activa' : 'Inactiva' }}</span></div>
          </template>
          <template #append>
            <v-btn size="small" variant="text" :disabled="!isAdmin" @click="openEdit(c)">Editar</v-btn>
            <v-btn size="small" variant="text" color="error" :disabled="!isAdmin" @click="remove(c.id)">Eliminar</v-btn>
          </template>
        </v-list-item>
      </v-list>
    </template>
    <v-dialog v-model="dlg" max-width="480">
      <v-card :title="editing ? 'Editar categoría' : 'Nueva categoría'">
        <v-card-text>
          <v-text-field v-model="form.name" label="Nombre *" :error-messages="fieldErr('name')" density="compact" />
          <v-text-field v-model.number="form.position" label="Posición" type="number" density="compact" :error-messages="fieldErr('position')" />
          <v-switch v-model="form.is_active" label="Activa" color="primary" />
          <v-alert v-if="formError" type="error" density="compact" class="mt-2">{{ formError }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer /><v-btn variant="text" @click="dlg=false">Cancelar</v-btn>
          <v-btn color="primary" :loading="saving" :disabled="!isAdmin" @click="save">Guardar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <ConfirmDialog v-model="confirm.show.value" :title="confirm.title.value" :message="confirm.message.value" :confirm-text="confirm.confirmText.value" :cancel-text="confirm.cancelText.value" :confirm-color="confirm.confirmColor.value" @confirm="confirm.onConfirm" @cancel="confirm.onCancel" />
  </v-container>
</template>
<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useAdminCategories, useCreateCategory, useUpdateCategory, useDeleteCategory, errDetails } from '@/composables/useAdminCatalog'
import { useAuthStore } from '@/stores/auth.store'
import { hasAnyRole } from '@/utils/guards'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { useConfirm, toast } from '@/composables/useConfirm'
const auth = useAuthStore()
const isAdmin = computed(() => hasAnyRole(auth.roles, ['ADMIN']))
const { data, isLoading, isError, error } = useAdminCategories()
const search = ref('')
const rawList = computed(() => (data.value as { id:number; name:string; position:number; is_active:boolean }[]) ?? [])
const list = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return rawList.value
  return rawList.value.filter(c => c.name.toLowerCase().startsWith(q))
})
const isForbidden = computed(() => (error.value as { response?: { status?: number } })?.response?.status === 403)
const dlg = ref(false); const editing = ref<number|null>(null); const saving = ref(false)
const form = reactive({ name: '', position: 0, is_active: true })
const details = ref<Record<string,string>>({}); const formError = ref('')
const fieldErr = (k: string) => details.value[k] ?? ''
const createM = useCreateCategory(); const updateM = useUpdateCategory(); const deleteM = useDeleteCategory()
function openCreate(){ editing.value=null; form.name=''; form.position=rawList.value.length; form.is_active=true; details.value={}; formError.value=''; dlg.value=true }
function openEdit(c: { id:number; name:string; position:number; is_active:boolean }){ editing.value=c.id; form.name=c.name; form.position=c.position; form.is_active=c.is_active; details.value={}; formError.value=''; dlg.value=true }
async function save(){
  if(!form.name.trim()){ details.value={ name:'Nombre requerido' }; return }
  saving.value=true; details.value={}; formError.value=''
  try{ if(editing.value) await updateM.mutateAsync({ id: editing.value, name: form.name, position: form.position, is_active: form.is_active } as never); else await createM.mutateAsync({ name: form.name, position: form.position, is_active: form.is_active } as never); dlg.value=false }
  catch(e: unknown){ const d=errDetails(e); if(Object.keys(d).length) details.value=d as Record<string,string>; else formError.value=(e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message ?? 'Error al guardar' }
  finally{ saving.value=false }
}
const confirm=useConfirm()
async function remove(id:number){ if(!await confirm.ask({ title:'¿Eliminar categoría?', message:'Esta acción no se puede deshacer.' })) return; try{ await deleteM.mutateAsync(id) } catch(e: unknown){ const s=(e as { response?: { status?: number } })?.response?.status; toast(s===403 ? '403 — Solo ADMIN' : 'Error al eliminar') } }
</script>
