<template>
  <v-container>
    <PageHeader title="Empleados" subtitle="Legajos, roles y estado">
      <v-btn color="primary" density="compact" prepend-icon="mdi-plus" :disabled="!isAdmin" @click="openCreate">Nuevo</v-btn>
    </PageHeader>
    <v-alert v-if="!isAdmin" type="warning" class="mb-4">Solo ADMIN gestiona empleados</v-alert>
    <v-alert v-if="isError && forbid" type="error" class="mb-4">403 — Solo ADMIN (BR-CIE-01)</v-alert>
    <DataTableCard
      v-model:search="search"
      :headers="headers"
      :items="list"
      :total="rawList.length"
      :search-keys="['fullname']"
      search-label="Buscar empleado"
      :loading="loading"
      no-data-text="Sin empleados"
    >
      <template #item.fullname="{ item }">
        <span class="font-weight-medium">{{ item.fullname ?? 'Sin nombre' }}</span>
      </template>
      <template #item.roles="{ item }">
        <span class="text-caption text-medium-emphasis">
          {{ ((item.roles ?? []) as string[]).join(', ') || 'sin rol' }}
        </span>
      </template>
      <template #item.is_active="{ item }">
        <StatusChip :value="Boolean(item.is_active)" positive="Activo" negative="Inactivo" />
      </template>
      <template #item.actions="{ item }">
        <v-btn icon="mdi-pencil" size="small" density="compact" variant="text" color="primary" title="Editar" :disabled="!isAdmin" @click="openEdit(item as never)" />
        <v-btn icon="mdi-delete" size="small" density="compact" variant="text" color="error" title="Eliminar" :disabled="!isAdmin" @click="remove(item.id as number)" />
      </template>
    </DataTableCard>
    <FormDialog
      v-model="dlg"
      :title="editing?'Editar empleado':'Nuevo empleado'"
      :max-width="480"
      :loading="saving"
      :submit-disabled="!isAdmin"
      @submit="save"
    >
      <v-text-field v-model="form.fullname" label="Nombre *" density="compact" :error-messages="details.fullname ?? ''" />
      <v-text-field v-model="form.cuil" label="CUIL *" density="compact" :error-messages="details.cuil ?? ''" />
      <v-text-field v-model="form.address" label="Dirección *" density="compact" :error-messages="details.address ?? ''" />
      <v-text-field v-model="form.city" label="Ciudad *" density="compact" :error-messages="details.city ?? ''" />
      <v-select v-model="form.roles" :items="roleOpts" label="Roles *" multiple chips density="compact" :error-messages="details.roles ?? ''" />
      <v-switch v-model="form.is_active" label="Activo" color="primary" />
      <v-alert v-if="formError" type="error" density="compact" class="mt-2">{{ formError }}</v-alert>
    </FormDialog>
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
import { DataTableCard, PageHeader, StatusChip } from '@/design'
import { useConfirm, toast } from '@/composables/useConfirm'
const auth = useAuthStore()
const isAdmin = computed(()=> hasAnyRole(auth.roles, ['ADMIN']))
const { data, isLoading: loading, isError, error } = useEmployees()
const search = ref('')
const rawList = computed(()=> (data.value as {id:number;fullname:string;is_active:boolean;roles:Role[]}[]) ?? [])
// Filtering happens inside DataTableCard (search-keys), so the table owns it.
const list = rawList
const headers = [
  { title: 'Nombre', key: 'fullname' },
  { title: 'Roles', key: 'roles' },
  { title: 'Estado', key: 'is_active', align: 'center' as const },
  { title: '', key: 'actions', sortable: false, align: 'end' as const },
]
const forbid = computed(()=> (error.value as {response?:{status?:number}})?.response?.status===403)
const roleOpts = [...ROLES]
const dlg=ref(false); const editing=ref<number|null>(null); const saving=ref(false)
const form=reactive({ fullname:'', cuil:'', address:'', city:'', is_active:true, roles:[] as Role[] })
const details=ref<Record<string,string>>({}); const formError=ref('')
const createM=useCreateEmployee(); const updateM=useUpdateEmployee(); const delM=useDeleteEmployee()
function openCreate(){ editing.value=null; form.fullname=''; form.cuil=''; form.address=''; form.city=''; form.is_active=true; form.roles=[]; details.value={}; formError.value=''; dlg.value=true }
function openEdit(e:{id:number;fullname:string;is_active:boolean;roles:Role[];cuil?:string;address?:string;city?:string}){ editing.value=e.id; form.fullname=e.fullname; form.cuil=e.cuil||''; form.address=e.address||''; form.city=e.city||''; form.is_active=e.is_active; form.roles=[...e.roles]; details.value={}; formError.value=''; dlg.value=true }
async function save(){
  if(!form.fullname.trim()){ details.value={ fullname:'Nombre requerido' }; return }
  if(!form.cuil.trim()){ details.value={ cuil:'CUIL requerido' }; return }
  if(!form.address.trim()){ details.value={ address:'Dirección requerida' }; return }
  if(!form.city.trim()){ details.value={ city:'Ciudad requerida' }; return }
  saving.value=true; details.value={}; formError.value=''
  try{ if(editing.value) await updateM.mutateAsync({ id: editing.value, fullname: form.fullname, is_active: form.is_active, roles: form.roles } as never); else await createM.mutateAsync({ fullname: form.fullname, is_active: form.is_active, roles: form.roles, cuil: form.cuil, address: form.address, city: form.city } as never); dlg.value=false }
  catch(e:unknown){ const d=empErrDetails(e); if(Object.keys(d).length) details.value=d as Record<string,string>; else formError.value=(e as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? 'Error' }
  finally{ saving.value=false }
}
const confirm=useConfirm()
async function remove(id:number){ if(!await confirm.ask({ title:'¿Eliminar empleado?', message:'Se hará soft-delete del empleado.' })) return; try{ await delM.mutateAsync(id) as never } catch(e:unknown){ toast((e as {response?:{status?:number}})?.response?.status===403?'403 Solo ADMIN':'Error') } }
</script>
