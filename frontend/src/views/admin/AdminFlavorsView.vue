<template>
  <v-container>
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 style="font-family:Comfortaa">Sabores</h2>
      <v-btn color="primary" @click="openCreate">Nuevo</v-btn>
    </div>
    <v-skeleton-loader v-if="isLoading" type="list-item@3" />
    <v-alert v-else-if="!list.length" type="info">Sin sabores — creá el primero</v-alert>
    <v-table v-else density="compact">
      <thead><tr><th>Nombre</th><th>Activo</th><th></th></tr></thead>
      <tbody>
        <tr v-for="f in list" :key="f.id">
          <td>{{ f.name }}</td><td>{{ f.is_active ? 'Sí' : 'No' }}</td>
          <td class="text-right"><v-btn size="small" variant="text" @click="openEdit(f)">Editar</v-btn><v-btn size="small" variant="text" color="error" @click="remove(f.id)">Eliminar</v-btn></td>
        </tr>
      </tbody>
    </v-table>
    <v-dialog v-model="dlg" max-width="480">
      <v-card :title="editing ? 'Editar sabor' : 'Nuevo sabor'">
        <v-card-text>
          <v-text-field v-model="form.name" label="Nombre *" :rules="[rRequired]" :error-messages="fieldErr('name')" density="compact" />
          <v-switch v-model="form.is_active" label="Activo" color="primary" />
          <v-alert v-if="formError" type="error" density="compact" class="mt-2">{{ formError }}</v-alert>
        </v-card-text>
        <v-card-actions><v-spacer/><v-btn variant="text" @click="dlg=false">Cancelar</v-btn><v-btn color="primary" :loading="saving" @click="save">Guardar</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>
<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useAdminFlavors, useCreateFlavor, useUpdateFlavor, useDeleteFlavor, errDetails } from '@/composables/useAdminCatalog'
import { qk } from '@/queries/keys'
const search = ref('')
const qkRef = computed(()=> qk.adminFlavors({ search: search.value || undefined }))
const { data, isLoading } = useAdminFlavors(computed(()=>undefined) as never, search as never)
const list = computed(()=>(data.value as {id:number;name:string;is_active?:boolean}[])??[])
const dlg=ref(false); const editing=ref<number|null>(null); const saving=ref(false)
const form=reactive({ name:'', is_active:true })
const details=ref<Record<string,string>>({}); const formError=ref('')
const fieldErr=(k:string)=>details.value[k]??''
const rRequired=(v:string)=>!!v||'Requerido'
const createM=useCreateFlavor(qkRef.value as never); const updateM=useUpdateFlavor(qkRef.value as never); const deleteM=useDeleteFlavor(qkRef.value as never)
function openCreate(){ editing.value=null; form.name=''; form.is_active=true; details.value={}; formError.value=''; dlg.value=true }
function openEdit(f: {id:number;name:string;is_active?:boolean}){ editing.value=f.id; form.name=f.name; form.is_active=f.is_active??true; details.value={}; formError.value=''; dlg.value=true }
async function save(){
  if(!form.name.trim()){ details.value={ name:'Nombre requerido' }; return }
  saving.value=true; details.value={}; formError.value=''
  const payload: Record<string,unknown>={ name:form.name, is_active: form.is_active }
  try{ if(editing.value) await updateM.mutateAsync({ id:editing.value, ...payload } as never); else await createM.mutateAsync(payload as never); dlg.value=false }
  catch(e: unknown){ const d=errDetails(e); if(Object.keys(d).length) details.value=d as Record<string,string>; else formError.value=(e as {response?:{data?:unknown}})?.response?.data ? JSON.stringify((e as {response:{data:unknown}}).response.data) : 'Error al guardar' }
  finally{ saving.value=false }
}
async function remove(id:number){ if(!confirm('¿Eliminar sabor?')) return; try{ await deleteM.mutateAsync(id as never) } catch{ alert('Error al eliminar') } }
</script>
