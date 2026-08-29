<template>
  <v-container>
    <h2 style="font-family:Comfortaa" class="mb-4">Horarios</h2>
    <v-alert v-if="!isAdmin" type="warning" class="mb-4">Solo ADMIN puede editar horarios</v-alert>
    <v-alert v-if="isError && forbid" type="error" class="mb-4">403 — Permiso denegado</v-alert>
    <v-skeleton-loader v-if="loading" type="list-item@4" />
    <template v-else>
      <v-row>
        <v-col v-for="d in days" :key="d.v" cols="12" md="6">
          <v-card :title="d.label" density="compact">
            <v-card-text>
              <div v-for="(r,i) in formByDay(d.v)" :key="i" class="d-flex ga-2 align-center mb-2">
                <v-text-field v-model="r.opens_at" label="Abre" type="time" density="compact" hide-details />
                <v-text-field v-model="r.closes_at" label="Cierra" type="time" density="compact" hide-details />
                <v-btn icon="mdi-close" size="x-small" variant="text" @click="removeRange(d.v,i)" />
              </div>
              <v-btn size="small" variant="text" @click="addRange(d.v)">+ Rango</v-btn>
              <v-alert v-if="overlapErr(d.v)" type="error" density="compact" class="mt-2">{{ overlapErr(d.v) }}</v-alert>
              <div class="mt-2 d-flex ga-2">
                <v-btn size="small" color="primary" :disabled="!isAdmin || !!overlapErr(d.v)" :loading="savingDay===d.v" @click="saveDay(d.v)">Guardar</v-btn>
                <v-btn size="small" variant="text" :disabled="!hasDay(d.v)" @click="delDay(d.v)">Borrar día</v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      <v-divider class="my-6" />
      <h3 style="font-family:Comfortaa" class="mb-2">Fechas especiales</h3>
      <v-alert v-if="sdError && forbidSd" type="error">403 — Permiso denegado</v-alert>
      <v-list v-if="sdList.length">
        <v-list-item v-for="s in sdList" :key="s.id" :title="`${s.date} — ${s.is_closed?'Cerrado':'Abierto'}`" :subtitle="s.reason">
          <template #append><v-btn size="small" variant="text" color="error" :disabled="!isAdmin" @click="delSd(s.id)">Eliminar</v-btn></template>
        </v-list-item>
      </v-list>
      <v-alert v-else type="info">Sin fechas especiales</v-alert>
      <v-card class="mt-4" title="Nueva fecha especial">
        <v-card-text class="d-flex flex-wrap ga-2 align-center">
          <v-text-field v-model="sdForm.date" label="Fecha" type="date" density="compact" hide-details style="max-width:200px" />
          <v-switch v-model="sdForm.is_closed" label="Cerrado" color="primary" hide-details />
          <v-text-field v-model="sdForm.reason" label="Motivo" density="compact" hide-details style="min-width:200px" :error-messages="sdDetails.reason ?? ''" />
          <v-btn color="primary" :disabled="!isAdmin || !sdForm.date" :loading="sdSaving" @click="createSd">Agregar</v-btn>
        </v-card-text>
        <v-card-text v-if="sdFormError"><v-alert type="error" density="compact">{{ sdFormError }}</v-alert></v-card-text>
      </v-card>
    </template>
    <ConfirmDialog v-model="confirm.show.value" :title="confirm.title.value" :message="confirm.message.value" :confirm-text="confirm.confirmText.value" :cancel-text="confirm.cancelText.value" :confirm-color="confirm.confirmColor.value" @confirm="confirm.onConfirm" @cancel="confirm.onCancel" />
  </v-container>
</template>
<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useSchedules, useSpecialDates, useUpsertSchedule, useDeleteSchedule, useCreateSpecialDate, useDeleteSpecialDate, errDetails } from '@/composables/useAdminOps'
import { useAuthStore } from '@/stores/auth.store'
import { hasAnyRole } from '@/utils/guards'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { useConfirm, toast } from '@/composables/useConfirm'
const auth = useAuthStore()
const isAdmin = computed(()=> hasAnyRole(auth.roles, ['ADMIN']))
const { data: schedData, isLoading: loading, isError, error } = useSchedules()
const { data: sdData, error: sdErr } = useSpecialDates()
const forbid = computed(()=> (error.value as {response?:{status?:number}})?.response?.status===403)
const forbidSd = computed(()=> (sdErr.value as {response?:{status?:number}})?.response?.status===403)
const sdError = computed(()=> !!sdErr.value)
const schedList = computed(()=> (schedData.value as {id:number;weekday:number;time_ranges:{opens_at:string;closes_at:string}[]}[]) ?? [])
const sdList = computed(()=> (sdData.value as {id:number;date:string;is_closed:boolean;reason:string}[]) ?? [])
const days = [{v:0,label:'Lunes'},{v:1,label:'Martes'},{v:2,label:'Miércoles'},{v:3,label:'Jueves'},{v:4,label:'Viernes'},{v:5,label:'Sábado'},{v:6,label:'Domingo'}]
const edits = reactive<Record<number,{opens_at:string;closes_at:string}[]>>({})
function formByDay(wd:number){
  if(!(wd in edits)){
    const ex=schedList.value.find(s=>s.weekday===wd)
    edits[wd]= ex ? ex.time_ranges.map(r=>({ ...r })) : []
  }
  return edits[wd]
}
function hasDay(wd:number){ return !!schedList.value.find(s=>s.weekday===wd) }
function addRange(wd:number){ formByDay(wd).push({ opens_at:'11:00', closes_at:'15:00' }) }
function removeRange(wd:number,i:number){ formByDay(wd).splice(i,1) }
function overlapErr(wd:number){
  const ranges=formByDay(wd)
  for(const r of ranges){ if(!r.opens_at||!r.closes_at) return 'Completa ambos horarios'; if(r.opens_at>=r.closes_at) return 'Apertura debe ser antes de cierre (BR-HRS-01)' }
  const s=[...ranges].sort((a,b)=>a.opens_at.localeCompare(b.opens_at))
  for(let i=1;i<s.length;i++) if(s[i].opens_at < s[i-1].closes_at) return 'Rangos no deben solaparse (BR-HRS-01)'
  return ''
}
const savingDay=ref<number|null>(null)
const upsertM=useUpsertSchedule(); const delM=useDeleteSchedule()
const confirm=useConfirm()
async function saveDay(wd:number){
  if(overlapErr(wd)) return
  savingDay.value=wd
  try{ await upsertM.mutateAsync({ weekday:wd, ranges: formByDay(wd)} as never); } catch(e:unknown){ const d=errDetails(e); toast(Object.values(d).join(', ') || (e as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message || 'Error') }
  finally{ savingDay.value=null }
}
async function delDay(wd:number){
  const s=schedList.value.find(x=>x.weekday===wd); if(!s) return; if(!await confirm.ask({ title:'¿Borrar horario del día?', message:'Se eliminarán todos los rangos de este día.' })) return
  try{ await delM.mutateAsync(s.id) as never; delete edits[wd] } catch(e:unknown){ toast((e as {response?:{status?:number}})?.response?.status===403?'403 Solo ADMIN':'Error') }
}
const sdForm=reactive({ date:'', is_closed:true, reason:'' }); const sdSaving=ref(false); const sdDetails=ref<Record<string,string>>({}); const sdFormError=ref('')
const createM=useCreateSpecialDate(); const delSdM=useDeleteSpecialDate()
async function createSd(){
  sdDetails.value={}; sdFormError.value=''; sdSaving.value=true
  try{ await createM.mutateAsync({ date: sdForm.date, is_closed: sdForm.is_closed, reason: sdForm.reason } as never); sdForm.date=''; sdForm.reason='' } catch(e:unknown){ const d=errDetails(e); if(Object.keys(d).length) sdDetails.value=d as Record<string,string>; else sdFormError.value=(e as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? 'Error' }
  finally{ sdSaving.value=false }
}
async function delSd(id:number){ if(!await confirm.ask({ title:'¿Eliminar fecha especial?', message:'Esta acción no se puede deshacer.' })) return; try{ await delSdM.mutateAsync(id) as never } catch(e:unknown){ toast((e as {response?:{status?:number}})?.response?.status===403?'403':'Error') } }
</script>
