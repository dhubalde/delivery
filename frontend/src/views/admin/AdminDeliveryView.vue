<template>
  <v-container>
    <h2 style="font-family:Comfortaa" class="mb-4">Delivery</h2>
    <v-alert v-if="!isAdmin" type="warning" class="mb-4">Solo ADMIN puede editar delivery</v-alert>
    <v-alert v-if="isError && forbid" type="error" class="mb-4">403 — Permiso denegado</v-alert>
    <v-skeleton-loader v-if="loading" type="card" />
    <template v-else>
      <v-card class="mb-6" title="Configuración (3 dimensiones)">
        <v-card-text>
          <v-row>
            <v-col cols="12" md="4"><v-select v-model="form.modo" :items="modoOpts" label="Modo" density="compact" :disabled="!isAdmin" /></v-col>
            <v-col cols="12" md="4"><v-select v-model="form.cobro" :items="cobroOpts" label="Cobro" density="compact" :disabled="!isAdmin" /></v-col>
            <v-col cols="12" md="4"><v-select v-model="form.calculo" :items="calculoOpts" label="Cálculo" density="compact" :disabled="!isAdmin" /></v-col>
            <v-col cols="12" md="4"><v-text-field v-model="form.flat_amount" label="Monto fijo" type="number" density="compact" :error-messages="details.flat_amount ?? ''" :disabled="!isAdmin" hide-details /></v-col>
            <v-col cols="12" md="4"><v-text-field v-model="form.free_threshold" label="Umbral gratis" type="number" density="compact" :error-messages="details.free_threshold ?? ''" :disabled="!isAdmin" hide-details /></v-col>
            <v-col cols="12" md="4"><v-text-field v-model="form.third_party_fixed_amount" label="Monto tercero fijo" type="number" density="compact" :error-messages="details.third_party_fixed_amount ?? ''" :disabled="!isAdmin" hide-details /></v-col>
          </v-row>
          <v-chip v-if="isPassthrough" color="info" class="mt-2">Passthrough: tercero+EN_PEDIDO → excluido de revenue (BR-DEL-04)</v-chip>
          <v-chip v-else-if="form.modo==='AMBOS' || form.cobro==='AMBOS'" color="warning" class="mt-2">AMBOS: permite ambos flujos — no es passthrough puro</v-chip>
          <v-alert v-if="saveErr" type="error" density="compact" class="mt-3">{{ saveErr }}</v-alert>
        </v-card-text>
        <v-card-actions><v-btn color="primary" :disabled="!isAdmin" :loading="saving" @click="saveCfg">Guardar config</v-btn></v-card-actions>
      </v-card>
      <h3 style="font-family:Comfortaa" class="mb-2">Zonas</h3>
      <v-skeleton-loader v-if="zLoading" type="list-item@3" />
      <v-list v-else-if="zones.length">
        <v-list-item v-for="z in zones" :key="z.id" :title="z.name" :subtitle="`$${z.base_fee}`">
          <template #append>
            <v-btn size="small" variant="text" :disabled="!isAdmin" @click="openEdit(z)">Editar</v-btn>
            <v-btn size="small" variant="text" color="error" :disabled="!isAdmin" @click="delZone(z.id)">Eliminar</v-btn>
          </template>
        </v-list-item>
      </v-list>
      <v-alert v-else type="info">Sin zonas — creá la primera</v-alert>
      <v-btn class="mt-3" color="primary" :disabled="!isAdmin" @click="openCreate">Nueva zona</v-btn>
      <v-dialog v-model="dlg" max-width="420">
        <v-card :title="editing?'Editar zona':'Nueva zona'">
          <v-card-text>
            <v-text-field v-model="zForm.name" label="Nombre *" density="compact" :error-messages="zDetails.name ?? ''" />
            <v-text-field v-model="zForm.base_fee" label="Base fee *" type="number" density="compact" :error-messages="zDetails.base_fee ?? ''" />
            <v-alert v-if="zFormError" type="error" density="compact">{{ zFormError }}</v-alert>
          </v-card-text>
          <v-card-actions><v-spacer/><v-btn variant="text" @click="dlg=false">Cancelar</v-btn><v-btn color="primary" :loading="zSaving" @click="saveZone">Guardar</v-btn></v-card-actions>
        </v-card>
      </v-dialog>
    </template>
    <ConfirmDialog v-model="confirm.show.value" :title="confirm.title.value" :message="confirm.message.value" :confirm-text="confirm.confirmText.value" :cancel-text="confirm.cancelText.value" :confirm-color="confirm.confirmColor.value" @confirm="confirm.onConfirm" @cancel="confirm.onCancel" />
  </v-container>
</template>
<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useDeliveryConfig, useZones, useUpdateDelivery, useCreateZone, useUpdateZone, useDeleteZone, errDetails, errStatus } from '@/composables/useAdminOps'
import { useAuthStore } from '@/stores/auth.store'
import { hasAnyRole } from '@/utils/guards'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { useConfirm, toast } from '@/composables/useConfirm'
const auth = useAuthStore()
const isAdmin = computed(()=> hasAnyRole(auth.roles, ['ADMIN']))
const { data: cfgData, isLoading: loading, isError, error } = useDeliveryConfig()
const { data: zData, isLoading: zLoading } = useZones()
const forbid = computed(()=> (error.value as {response?:{status?:number}})?.response?.status===403)
const cfg = computed(()=> cfgData.value as { modo: string; cobro: string; calculo: string; flat_amount: string|null; free_threshold: string|null; third_party_fixed_amount: string|null } | undefined)
const zones = computed(()=> (zData.value as {id:number;name:string;base_fee:string}[]) ?? [])
const modoOpts=['PROPIO','TERCERIZADO','AMBOS']; const cobroOpts=['EN_PEDIDO','EN_ENTREGA','AMBOS']; const calculoOpts=['POR_ZONA','FIJO','GRATIS_MONTO','POR_DISTANCIA']
const form=reactive({ modo:'PROPIO', cobro:'EN_PEDIDO', calculo:'FIJO', flat_amount:'', free_threshold:'', third_party_fixed_amount:'' })
watch(cfg, v=>{ if(v){ form.modo=v.modo; form.cobro=v.cobro; form.calculo=v.calculo; form.flat_amount=v.flat_amount ?? ''; form.free_threshold=v.free_threshold ?? ''; form.third_party_fixed_amount=v.third_party_fixed_amount ?? '' } }, { immediate:true })
const isPassthrough = computed(()=> form.modo==='TERCERIZADO' && form.cobro==='EN_PEDIDO')
const details=ref<Record<string,string>>({}); const saveErr=ref(''); const saving=ref(false)
const updM=useUpdateDelivery()
async function saveCfg(){
  saving.value=true; details.value={}; saveErr.value=''
  const payload:Record<string,unknown>={ modo: form.modo, cobro: form.cobro, calculo: form.calculo, flat_amount: form.flat_amount||null, free_threshold: form.free_threshold||null, third_party_fixed_amount: form.third_party_fixed_amount||null }
  try{ await updM.mutateAsync(payload as never) } catch(e:unknown){
    const s=errStatus(e); const d=errDetails(e)
    if(s===409) saveErr.value='409 CONFIG_IMMUTABLE — config bloqueada con pedidos activos (BR-DEL-05)'
    else if(Object.keys(d).length) details.value=d as Record<string,string>
    else saveErr.value=(e as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? 'Error al guardar'
  } finally{ saving.value=false }
}
const dlg=ref(false); const editing=ref<number|null>(null); const zSaving=ref(false)
const zForm=reactive({ name:'', base_fee:'' }); const zDetails=ref<Record<string,string>>({}); const zFormError=ref('')
const createM=useCreateZone(); const updateM=useUpdateZone(); const delM=useDeleteZone()
function openCreate(){ editing.value=null; zForm.name=''; zForm.base_fee=''; zDetails.value={}; zFormError.value=''; dlg.value=true }
function openEdit(z:{id:number;name:string;base_fee:string}){ editing.value=z.id; zForm.name=z.name; zForm.base_fee=z.base_fee; zDetails.value={}; zFormError.value=''; dlg.value=true }
async function saveZone(){
  if(!zForm.name.trim()){ zDetails.value={ name:'Nombre requerido' }; return }
  if(!zForm.base_fee) { zDetails.value={ base_fee:'Base fee requerido' }; return }
  zSaving.value=true; zDetails.value={}; zFormError.value=''
  try{ if(editing.value) await updateM.mutateAsync({ id: editing.value, name: zForm.name, base_fee: zForm.base_fee } as never); else await createM.mutateAsync({ name: zForm.name, base_fee: zForm.base_fee } as never); dlg.value=false }
  catch(e:unknown){ const d=errDetails(e); if(Object.keys(d).length) zDetails.value=d as Record<string,string>; else zFormError.value=(e as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? 'Error' }
  finally{ zSaving.value=false }
}
const confirm=useConfirm()
async function delZone(id:number){ if(!await confirm.ask({ title:'¿Eliminar zona?', message:'Esta acción no se puede deshacer.' })) return; try{ await delM.mutateAsync(id) as never } catch(e:unknown){ toast((e as {response?:{status?:number}})?.response?.status===403?'403 Solo ADMIN':'Error al eliminar') } }
</script>
