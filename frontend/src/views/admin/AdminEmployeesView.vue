<template>
  <v-container>
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 style="font-family:Comfortaa">Empleados</h2>
      <v-btn color="primary" :disabled="!isAdmin" @click="openCreate">Nuevo</v-btn>
    </div>
    <v-alert v-if="!isAdmin" type="warning" class="mb-4">Solo ADMIN gestiona empleados</v-alert>
    <v-alert v-if="isError && forbid" type="error" class="mb-4">403 — Solo ADMIN (BR-CIE-01)</v-alert>
    <v-skeleton-loader v-if="loading" type="list-item@3" />
    <v-alert v-else-if="!list.length" type="info">Sin empleados</v-alert>
    <v-list v-else>
      <v-list-item v-for="e in list" :key="e.id" :title="e.display_name" :subtitle="`${e.roles.join(', ') || 'sin rol'} · ${e.is_active ? 'Activo' : 'Inactivo'}`">
        <template #append>
          <v-btn size="small" variant="text" :disabled="!isAdmin" @click="openEdit(e)">Editar</v-btn>
          <v-btn size="small" variant="text" color="error" :disabled="!isAdmin" @click="remove(e.id)">Eliminar</v-btn>
        </template>
      </v-list-item>
    </v-list>
    <v-dialog v-model="dlg" max-width="480">
      <v-card :title="editing?'Editar empleado':'Nuevo empleado'">
        <v-card-text>
          <v-text-field v-model="form.display_name" label="Nombre *" density="compact" :error-messages="details.display_name ?? ''" />
          <v-select v-model="form.roles" :items="roleOpts" label="Roles *" multiple chips density="compact" :error-messages="details.roles ?? ''" />
          <v-switch v-model="form.is_active" label="Activo" color="primary" />
          <v-alert v-if="formError" type="error" density="compact" class="mt-2">{{ formError }}</v-alert>
        </v-card-text>
        <v-card-actions><v-spacer/><v-btn variant="text" @click="dlg=false">Cancelar</v-btn><v-btn color="primary" :loading="saving" :disabled="!isAdmin" @click="save">Guardar</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
    <ConfirmDialog v-model="confirm.show.value" :title="confirm.title.value" :message="confirm.message.value" :confirm-text="confirm.confirmText.value" :cancel-text="confirm.cancelText.value" :confirm-color="confirm.confirmColor.value" @confirm="confirm.onConfirm" @cancel="confirm.onCancel" />
  </v-container>
</template>
<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useEmployees, useCreateEmployee, useUpdateEmployee, useDeleteEmployee, empErrDetails } from '@/composables/useAdminEmployees'
import { ROLES, type Role } from '@/api/panel/employees.api'
import { useAuthStore } from '@/stores/auth.store'
import { hasAnyRole } from '@/utils/guards'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { useConfirm, toast } from '@/composables/useConfirm'
const auth = useAuthStore()
const isAdmin = computed(()=> hasAnyRole(auth.roles, ['ADMIN']))
const { data, isLoading: loading, isError, error } = useEmployees()
const list = computed(()=> (data.value as {id:number;display_name:string;is_active:boolean;roles:Role[]}[]) ?? [])
const forbid = computed(()=> (error.value as {response?:{status?:number}})?.response?.status===403)
const roleOpts = [...ROLES]
const dlg=ref(false); const editing=ref<number|null>(null); const saving=ref(false)
const form=reactive({ display_name:'', is_active:true, roles:[] as Role[] })
const details=ref<Record<string,string>>({}); const formError=ref('')
const createM=useCreateEmployee(); const updateM=useUpdateEmployee(); const delM=useDeleteEmployee()
function openCreate(){ editing.value=null; form.display_name=''; form.is_active=true; form.roles=[]; details.value={}; formError.value=''; dlg.value=true }
function openEdit(e:{id:number;display_name:string;is_active:boolean;roles:Role[]}){ editing.value=e.id; form.display_name=e.display_name; form.is_active=e.is_active; form.roles=[...e.roles]; details.value={}; formError.value=''; dlg.value=true }
async function save(){
  if(!form.display_name.trim()){ details.value={ display_name:'Nombre requerido' }; return }
  saving.value=true; details.value={}; formError.value=''
  try{ if(editing.value) await updateM.mutateAsync({ id: editing.value, display_name: form.display_name, is_active: form.is_active, roles: form.roles } as never); else await createM.mutateAsync({ display_name: form.display_name, is_active: form.is_active, roles: form.roles } as never); dlg.value=false }
  catch(e:unknown){ const d=empErrDetails(e); if(Object.keys(d).length) details.value=d as Record<string,string>; else formError.value=(e as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? 'Error' }
  finally{ saving.value=false }
}
const confirm=useConfirm()
async function remove(id:number){ if(!await confirm.ask({ title:'¿Eliminar empleado?', message:'Se hará soft-delete del empleado.' })) return; try{ await delM.mutateAsync(id) as never } catch(e:unknown){ toast((e as {response?:{status?:number}})?.response?.status===403?'403 Solo ADMIN':'Error') } }
</script>
