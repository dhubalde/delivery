<template>
  <v-container>
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 style="font-family:Comfortaa">Categorías</h2>
      <v-btn color="primary" @click="openCreate">Nueva</v-btn>
    </div>
    <v-skeleton-loader v-if="isLoading" type="list-item@3" />
    <v-alert v-else-if="!list.length" type="info">Sin categorías — creá la primera</v-alert>
    <v-table v-else density="compact">
      <thead><tr><th>Nombre</th><th>Posición</th><th>Activo</th><th></th></tr></thead>
      <tbody>
        <tr v-for="c in list" :key="c.id">
          <td>{{ c.name }}</td><td>#{{ c.position }}</td><td>{{ c.is_active ? 'Sí' : 'No' }}</td>
          <td class="text-right"><v-btn size="small" variant="text" @click="openEdit(c)">Editar</v-btn><v-btn size="small" variant="text" color="error" @click="remove(c.id)">Eliminar</v-btn></td>
        </tr>
      </tbody>
    </v-table>
    <v-dialog v-model="dlg" max-width="480">
      <v-card :title="editing ? 'Editar categoría' : 'Nueva categoría'">
        <v-card-text>
          <v-text-field v-model="form.name" label="Nombre *" :rules="[rRequired]" :error-messages="fieldErr('name')" density="compact" />
          <v-text-field v-model.number="form.position" label="Posición" type="number" density="compact" :error-messages="fieldErr('position')" />
          <v-switch v-model="form.is_active" label="Activa" color="primary" />
          <v-alert v-if="formError" type="error" density="compact" class="mt-2">{{ formError }}</v-alert>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn variant="text" @click="dlg=false">Cancelar</v-btn><v-btn color="primary" :loading="saving" @click="save">Guardar</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>
<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useAdminCategories, useCreateCategory, useUpdateCategory, useDeleteCategory, errDetails } from '@/composables/useAdminCatalog'
const { data, isLoading } = useAdminCategories()
const list = computed(() => (data.value as { id:number; name:string; position:number; is_active:boolean }[]) ?? [])
const dlg = ref(false); const editing = ref<number|null>(null); const saving = ref(false)
const form = reactive({ name: '', position: 0, is_active: true })
const details = ref<Record<string,string>>({}); const formError = ref('')
const fieldErr = (k: string) => details.value[k] ?? ''
const rRequired = (v: string) => !!v || 'Requerido'
const createM = useCreateCategory(); const updateM = useUpdateCategory(); const deleteM = useDeleteCategory()
function openCreate(){ editing.value=null; form.name=''; form.position=list.value.length; form.is_active=true; details.value={}; formError.value=''; dlg.value=true }
function openEdit(c: { id:number; name:string; position:number; is_active:boolean }){ editing.value=c.id; form.name=c.name; form.position=c.position; form.is_active=c.is_active; details.value={}; formError.value=''; dlg.value=true }
async function save(){
  if(!form.name.trim()){ details.value={ name:'Nombre requerido' }; return }
  saving.value=true; details.value={}; formError.value=''
  try{ if(editing.value) await updateM.mutateAsync({ id: editing.value, name: form.name, position: form.position, is_active: form.is_active } as never); else await createM.mutateAsync({ name: form.name, position: form.position, is_active: form.is_active } as never); dlg.value=false }
  catch(e: unknown){ const d=errDetails(e); if(Object.keys(d).length) details.value=d as Record<string,string>; else formError.value=(e as { response?: { data?: unknown } })?.response?.data ? JSON.stringify((e as { response:{data:unknown}}).response.data) : 'Error al guardar' }
  finally{ saving.value=false }
}
async function remove(id:number){ if(!confirm('¿Eliminar categoría?')) return; try{ await deleteM.mutateAsync(id as never) } catch{ alert('Error al eliminar') } }
</script>
