<template>
  <v-container>
    <PageHeader title="Categorías" subtitle="Orden y visibilidad del catálogo">
      <v-btn color="primary" density="compact" prepend-icon="mdi-plus" :disabled="!isAdmin" @click="openCreate">Nueva</v-btn>
    </PageHeader>
    <v-alert v-if="!isAdmin" type="warning" class="mb-4">Solo ADMIN puede editar categorías</v-alert>
    <v-alert v-if="isError && isForbidden" type="error">403 — Permiso denegado (ADMIN requerido)</v-alert>
    <DataTableCard
      v-model:search="search"
      :headers="headers"
      :items="list"
      :total="rawList.length"
      :search-keys="['name']"
      search-label="Buscar categoría"
      :loading="isLoading"
      no-data-text="Sin categorías — creá la primera"
    >
      <template #item.name="{ item }">
        <span class="font-weight-medium">{{ item.name }}</span>
      </template>
      <template #item.position="{ item }">
        <span class="text-medium-emphasis">#{{ item.position }}</span>
      </template>
      <template #item.is_active="{ item }">
        <StatusChip :value="Boolean(item.is_active)" positive="Activa" negative="Inactiva" />
      </template>
      <template #item.actions="{ item }">
        <v-btn icon="mdi-pencil" size="small" density="compact" variant="text" color="primary" title="Editar" :disabled="!isAdmin" @click="openEdit(item)" />
        <v-btn icon="mdi-delete" size="small" density="compact" variant="text" color="error" title="Eliminar" :disabled="!isAdmin" @click="remove(item.id as number)" />
      </template>
    </DataTableCard>
    <FormDialog
      v-model="dlg"
      :title="editing ? 'Editar categoría' : 'Nueva categoría'"
      :max-width="480"
      :loading="saving"
      :submit-disabled="!isAdmin"
      @submit="save"
    >
      <v-text-field v-model="form.name" label="Nombre *" :error-messages="fieldErr('name')" density="compact" />
      <v-text-field v-model.number="form.position" label="Posición" type="number" density="compact" :error-messages="fieldErr('position')" />
      <v-switch v-model="form.is_active" label="Activa" color="primary" />
      <v-alert v-if="formError" type="error" density="compact" class="mt-2">{{ formError }}</v-alert>
    </FormDialog>
    <ConfirmDialog v-model="confirm.show.value" :title="confirm.title.value" :message="confirm.message.value" :confirm-text="confirm.confirmText.value" :cancel-text="confirm.cancelText.value" :confirm-color="confirm.confirmColor.value" @confirm="confirm.onConfirm" @cancel="confirm.onCancel" />
  </v-container>
</template>
<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useAdminCategories, useCreateCategory, useUpdateCategory, useDeleteCategory, errDetails } from '@/composables/useAdminCatalog'
import { useAuthStore } from '@/stores/auth.store'
import { hasAnyRole } from '@/utils/guards'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { DataTableCard, PageHeader, StatusChip } from '@/design'
import { useConfirm, toast } from '@/composables/useConfirm'
const auth = useAuthStore()
const isAdmin = computed(() => hasAnyRole(auth.roles, ['ADMIN']))
const { data, isLoading, isError, error } = useAdminCategories()
const search = ref('')
const rawList = computed(() => (data.value as { id:number; name:string; position:number; is_active:boolean }[]) ?? [])
// Filtering happens inside DataTableCard (search-keys), so the table owns it.
const list = rawList
const headers = [
  { title: 'Nombre', key: 'name' },
  { title: 'Posición', key: 'position', align: 'end' as const },
  { title: 'Estado', key: 'is_active', align: 'center' as const },
  { title: '', key: 'actions', sortable: false, align: 'end' as const },
]
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
