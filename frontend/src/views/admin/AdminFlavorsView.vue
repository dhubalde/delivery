<template>
  <v-container>
    <div class="d-flex align-center justify-space-between mb-1 flex-wrap ga-2">
      <div>
        <h2 class="text-h6" style="font-family:Comfortaa">Sabores</h2>
        <div class="text-caption text-medium-emphasis">Gustos por categoría o globales</div>
      </div>
      <v-btn color="primary" density="compact" prepend-icon="mdi-plus" :disabled="!isAdmin" @click="openCreate">Nuevo</v-btn>
    </div>
    <v-alert v-if="!isAdmin" type="warning" class="mb-4">Solo ADMIN puede editar sabores</v-alert>
    <v-card variant="tonal" class="mb-3">
      <v-card-text class="d-flex flex-wrap ga-2 align-center py-2">
        <v-text-field v-model="search" label="Buscar" prepend-inner-icon="mdi-magnify" clearable density="compact" hide-details style="max-width:260px" />
        <v-select v-model="fltCat" :items="catItems" label="Categoría" clearable density="compact" hide-details style="max-width:220px" />
      </v-card-text>
    </v-card>
    <v-alert v-if="isForbidden" type="error" class="mb-2">403 — ADMIN requerido</v-alert>
    <v-skeleton-loader v-if="isLoading" type="list-item@3" />
    <v-alert v-else-if="!list.length" type="info">Sin sabores — creá el primero</v-alert>
    <template v-else>
      <v-table density="compact" fixed-header hover>
        <thead>
          <tr><th>Nombre</th><th>Categoría</th><th class="text-right">Acciones</th></tr>
        </thead>
        <tbody>
          <tr v-for="f in list" :key="f.id">
            <td class="font-weight-medium">{{ f.name }}</td>
            <td class="text-caption text-medium-emphasis">{{ catName(f.category_id) }}</td>
            <td class="text-right text-no-wrap">
              <v-btn icon="mdi-pencil" size="small" density="compact" variant="text" title="Editar" :disabled="!isAdmin" @click="openEdit(f)" />
              <v-btn icon="mdi-delete" size="small" density="compact" variant="text" color="error" title="Eliminar" :disabled="!isAdmin" @click="remove(f.id)" />
            </td>
          </tr>
        </tbody>
      </v-table>
    </template>
    <v-dialog v-model="dlg" max-width="480">
      <v-card :title="editing ? 'Editar sabor' : 'Nuevo sabor'">
        <v-card-text>
          <v-text-field v-model="form.name" label="Nombre *" :error-messages="fieldErr('name')" density="compact" />
          <v-select v-model="form.category_id" :items="catItems" label="Categoría (opcional)" clearable :error-messages="fieldErr('category_id')" density="compact" />
          <v-switch v-model="form.is_active" label="Activo" color="primary" />
          <v-alert v-if="formError" type="error" density="compact" class="mt-2">{{ formError }}</v-alert>
        </v-card-text>
        <v-card-actions><v-spacer/><v-btn variant="text" density="compact" @click="dlg=false">Cancelar</v-btn><v-btn color="primary" density="compact" :loading="saving" :disabled="!isAdmin" @click="save">Guardar</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
    <ConfirmDialog v-model="confirm.show.value" :title="confirm.title.value" :message="confirm.message.value" :confirm-text="confirm.confirmText.value" :cancel-text="confirm.cancelText.value" :confirm-color="confirm.confirmColor.value" @confirm="confirm.onConfirm" @cancel="confirm.onCancel" />
  </v-container>
</template>
<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useAdminCategories, useAdminFlavors, useCreateFlavor, useUpdateFlavor, useDeleteFlavor, errDetails } from '@/composables/useAdminCatalog'
import { useAuthStore } from '@/stores/auth.store'
import { hasAnyRole } from '@/utils/guards'
import { qk } from '@/queries/keys'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { useConfirm, toast } from '@/composables/useConfirm'
const auth = useAuthStore(); const isAdmin = computed(()=>hasAnyRole(auth.roles,['ADMIN']))
const { data: cats } = useAdminCategories()
const catItems = computed(()=>((cats.value as {id:number;name:string}[])??[]).map(c=>({ title:c.name, value:c.id })))
const catMap = computed(()=>Object.fromEntries(((cats.value as {id:number;name:string}[])??[]).map(c=>[c.id,c.name])))
const catName = (id: number|null) => id ? (catMap.value[id] ?? `Cat #${id}`) : 'Sin categoría (global)'
const fltCat = ref<number|undefined>(undefined); const search = ref('')
const qkRef = computed(()=> qk.adminFlavors({ category: fltCat.value, search: search.value || undefined }))
const { data, isLoading, error } = useAdminFlavors(fltCat as never, search as never)
const list = computed(()=>(data.value as {id:number;name:string;category_id:number|null}[])??[])
const isForbidden = computed(()=>(error.value as {response?:{status?:number}})?.response?.status===403)
const dlg=ref(false); const editing=ref<number|null>(null); const saving=ref(false)
const form=reactive({ name:'', category_id: null as number|null, is_active:true })
const details=ref<Record<string,string>>({}); const formError=ref('')
const fieldErr=(k:string)=>details.value[k]??''
const createM=useCreateFlavor(qkRef.value as never); const updateM=useUpdateFlavor(qkRef.value as never); const deleteM=useDeleteFlavor(qkRef.value as never)
function openCreate(){ editing.value=null; form.name=''; form.category_id=null; form.is_active=true; details.value={}; formError.value=''; dlg.value=true }
function openEdit(f: {id:number;name:string;category_id:number|null;is_active?:boolean}){ editing.value=f.id; form.name=f.name; form.category_id=f.category_id; form.is_active=f.is_active??true; details.value={}; formError.value=''; dlg.value=true }
async function save(){
  if(!form.name.trim()){ details.value={ name:'Nombre requerido' }; return }
  saving.value=true; details.value={}; formError.value=''
  const payload: Record<string,unknown>={ name:form.name, category_id: form.category_id ?? null, is_active: form.is_active }
  try{ if(editing.value) await updateM.mutateAsync({ id:editing.value, ...payload } as never); else await createM.mutateAsync(payload as never); dlg.value=false }
  catch(e: unknown){ const d=errDetails(e); if(Object.keys(d).length) details.value=d as Record<string,string>; else formError.value=(e as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? 'Error al guardar (¿nombre duplicado?)' }
  finally{ saving.value=false }
}
const confirm=useConfirm()
async function remove(id:number){ if(!await confirm.ask({ title:'¿Eliminar sabor?', message:'Esta acción no se puede deshacer.' })) return; try{ await deleteM.mutateAsync(id) } catch(e: unknown){ toast((e as {response?:{status?:number}})?.response?.status===403 ? '403 — Solo ADMIN' : 'Error al eliminar') } }
</script>
