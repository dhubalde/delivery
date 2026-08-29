<template>
  <v-container>
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 style="font-family:Comfortaa">Productos</h2>
      <v-btn color="primary" :disabled="!isAdmin" @click="openCreate">Nuevo</v-btn>
    </div>
    <v-alert v-if="!isAdmin" type="warning" class="mb-4">Solo ADMIN puede editar productos</v-alert>
    <v-row class="mb-4">
      <v-col cols="12" md="4"><v-select v-model="fltCat" :items="catItems" label="Filtrar por categoría" clearable density="compact" /></v-col>
      <v-col cols="12" md="4"><v-text-field v-model="search" label="Buscar (prefix)" clearable density="compact" /></v-col>
    </v-row>
    <v-alert v-if="isForbidden" type="error" class="mb-2">403 — ADMIN requerido</v-alert>
    <v-skeleton-loader v-if="isLoading" type="list-item@3" />
    <v-alert v-else-if="!list.length" type="info">Sin productos — ajustá filtros o creá uno</v-alert>
    <v-list v-else>
      <v-list-item v-for="p in list" :key="p.id" :title="p.name" :subtitle="`${p.product_type} ${p.pote_size ?? ''} $${p.price}`">
        <template #append>
          <v-btn size="small" variant="text" :disabled="!isAdmin" @click="openEdit(p as never)">Editar</v-btn>
          <v-btn size="small" variant="text" color="error" :disabled="!isAdmin" @click="remove(p.id)">Eliminar</v-btn>
        </template>
      </v-list-item>
    </v-list>
    <v-dialog v-model="dlg" max-width="520">
      <v-card :title="editing ? 'Editar producto' : 'Nuevo producto'">
        <v-card-text>
          <v-text-field v-model="form.name" label="Nombre *" :error-messages="fieldErr('name')" density="compact" />
          <v-select v-model="form.category_id" :items="catItems" label="Categoría *" :error-messages="fieldErr('category_id')" density="compact" />
          <v-select v-model="form.product_type" :items="['POTE','UNIT']" label="Tipo *" density="compact" />
          <v-select v-if="form.product_type==='POTE'" v-model="form.pote_size" :items="poteSizeItems" label="Tamaño pote *" :error-messages="fieldErr('pote_size')" density="compact" />
          <v-checkbox v-model="form.has_flavors" label="Permite elegir gustos" density="compact" hide-details />
          <v-row v-if="form.has_flavors">
            <v-col><v-text-field v-model.number="form.min_flavors" label="Min gustos" type="number" density="compact" :error-messages="fieldErr('min_flavors')" /></v-col>
            <v-col><v-text-field v-model.number="form.max_flavors" label="Max gustos" type="number" density="compact" :error-messages="fieldErr('max_flavors')" /></v-col>
          </v-row>
          <v-text-field v-model="form.price" label="Precio *" prefix="$" density="compact" :error-messages="fieldErr('price')" />
          <v-alert v-if="poteHint" type="info" density="compact" class="mt-2">{{ poteHint }}</v-alert>
          <v-alert v-if="formError" type="error" density="compact" class="mt-2">{{ formError }}</v-alert>
        </v-card-text>
        <v-card-actions><v-spacer/><v-btn variant="text" @click="dlg=false">Cancelar</v-btn><v-btn color="primary" :loading="saving" :disabled="!isAdmin" @click="save">Guardar</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
    <ConfirmDialog v-model="confirm.show.value" :title="confirm.title.value" :message="confirm.message.value" :confirm-text="confirm.confirmText.value" :cancel-text="confirm.cancelText.value" :confirm-color="confirm.confirmColor.value" @confirm="confirm.onConfirm" @cancel="confirm.onCancel" />
  </v-container>
</template>
<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useAdminCategories, useAdminProducts, useCreateProduct, useUpdateProduct, useDeleteProduct, errDetails } from '@/composables/useAdminCatalog'
import { useAuthStore } from '@/stores/auth.store'
import { hasAnyRole } from '@/utils/guards'
import { qk } from '@/queries/keys'
import { hint } from '@/utils/flavorPolicy'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { useConfirm, toast } from '@/composables/useConfirm'
const auth = useAuthStore(); const isAdmin = computed(()=>hasAnyRole(auth.roles,['ADMIN']))
const { data: cats } = useAdminCategories()
const catItems = computed(()=>((cats.value as {id:number;name:string}[])??[]).map(c=>({ title:c.name, value:c.id })))
const poteSizeItems = [{ title: '1 kg', value: 'KG_1' }, { title: '1/2 kg', value: 'KG_HALF' }, { title: '1/4 kg', value: 'KG_QUARTER' }]
const fltCat = ref<number|undefined>(undefined); const search = ref('')
const qkRef = computed(()=> qk.adminProducts({ category: fltCat.value, search: search.value || undefined }))
const { data, isLoading, error } = useAdminProducts(fltCat as never, search as never)
const list = computed(()=>(data.value as {id:number;name:string;product_type:string;pote_size:string|null;price:string}[])??[])
const isForbidden = computed(()=>(error.value as { response?:{status?:number}})?.response?.status===403)
const dlg=ref(false); const editing=ref<number|null>(null); const saving=ref(false)
const form=reactive({ name:'', category_id: null as number|null, product_type:'POTE' as 'POTE'|'UNIT', pote_size:'KG_1' as 'KG_1'|'KG_HALF'|'KG_QUARTER'|null, has_flavors:true, min_flavors:1 as number|null, max_flavors:4 as number|null, price:'' })
const details=ref<Record<string,string>>({}); const formError=ref('')
const fieldErr=(k:string)=>details.value[k]??''
const poteHint=computed(()=> form.has_flavors ? hint(form.pote_size, form.product_type) : '')
const createM=useCreateProduct(qkRef.value as never); const updateM=useUpdateProduct(qkRef.value as never); const deleteM=useDeleteProduct(qkRef.value as never)
watch(()=>form.has_flavors, (v)=>{ if(v && (form.min_flavors==null || form.max_flavors==null)){ if(form.pote_size==='KG_QUARTER'){ form.min_flavors=1; form.max_flavors=3 } else { form.min_flavors=1; form.max_flavors=4 } } })
watch(()=>form.pote_size, (v)=>{ if(!form.has_flavors) return; if(v==='KG_QUARTER' && form.min_flavors===3 && form.max_flavors===4){ form.min_flavors=1; form.max_flavors=3 } })
watch(()=>form.product_type, (v)=>{ if(v==='UNIT'){ form.pote_size=null } else if(v==='POTE' && !form.pote_size){ form.pote_size='KG_1' } })
function openCreate(){ editing.value=null; Object.assign(form,{ name:'', category_id:null, product_type:'POTE', pote_size:'KG_1', has_flavors:true, min_flavors:1, max_flavors:4, price:'' }); details.value={}; formError.value=''; dlg.value=true }
function openEdit(p: {id:number;name:string;category_id:number;product_type:'POTE'|'UNIT';pote_size:'KG_1'|'KG_HALF'|'KG_QUARTER'|null;min_flavors:number|null;max_flavors:number|null;price:string}){ const has = p.min_flavors!=null && p.max_flavors!=null; editing.value=p.id; Object.assign(form,{ name:p.name, category_id:p.category_id, product_type:p.product_type, pote_size:p.pote_size, has_flavors:has, min_flavors:p.min_flavors ?? 1, max_flavors:p.max_flavors ?? 4, price:p.price }); details.value={}; formError.value=''; dlg.value=true }
function validatePote(): string|null{
  if(form.product_type==='UNIT'){ if(form.pote_size) return 'UNIT no permite pote_size'; if(form.has_flavors){ if(form.min_flavors==null || form.max_flavors==null) return 'Min/max requeridos cuando tiene gustos'; if(form.min_flavors<1 || form.max_flavors>4 || form.min_flavors>form.max_flavors) return 'Requiere 1 <= min <= max <= 4' } return null }
  if(!form.pote_size) return 'Tamaño requerido para POTE'
  if(!form.has_flavors) return null
  if(form.min_flavors==null || form.max_flavors==null) return 'Min/max requeridos cuando tiene gustos'
  if(form.min_flavors<1 || form.max_flavors>4 || form.min_flavors>form.max_flavors) return 'Requiere 1 <= min <= max <= 4'
  return null
}
async function save(){
  const v=validatePote(); if(v){ formError.value=v; return }
  if(!form.category_id){ details.value={...details.value, category_id:'Elegí una categoría'}; return }
  if(!form.name.trim() || !form.price){ details.value={ ...(!form.name.trim()?{name:'Nombre requerido'}:{}), ...(!form.price?{price:'Precio requerido'}:{}) }; return }
  saving.value=true; details.value={}; formError.value=''
  const payload: Record<string,unknown>={ name:form.name, category_id:form.category_id, product_type:form.product_type, pote_size: form.product_type==='UNIT'?null:form.pote_size, min_flavors: form.has_flavors?form.min_flavors:null, max_flavors: form.has_flavors?form.max_flavors:null, price:form.price }
  try{ if(editing.value) await updateM.mutateAsync({ id:editing.value, ...payload } as never); else await createM.mutateAsync(payload as never); dlg.value=false }
  catch(e: unknown){ const d=errDetails(e); if(Object.keys(d).length) details.value=d as Record<string,string>; else formError.value=(e as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? 'Error al guardar' }
  finally{ saving.value=false }
}
const confirm=useConfirm()
async function remove(id:number){ if(!await confirm.ask({ title:'¿Eliminar producto?', message:'Esta acción no se puede deshacer.' })) return; try{ await deleteM.mutateAsync(id) } catch(e: unknown){ toast((e as {response?:{status?:number}})?.response?.status===403 ? '403 — Solo ADMIN' : 'Error al eliminar') } }
</script>
