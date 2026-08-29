<template>
  <v-container>
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 style="font-family:Comfortaa">Productos</h2>
      <v-btn color="primary" @click="openCreate">Nuevo</v-btn>
    </div>
    <v-row class="mb-4">
      <v-col cols="12" md="4"><v-select v-model="fltCat" :items="catItems" label="Filtrar por categoría" clearable density="compact" /></v-col>
      <v-col cols="12" md="4"><v-text-field v-model="search" label="Buscar" clearable density="compact" /></v-col>
    </v-row>
    <v-skeleton-loader v-if="isLoading" type="list-item@3" />
    <v-alert v-else-if="!list.length" type="info">Sin productos</v-alert>
    <v-table v-else density="compact">
      <thead><tr><th>Descripción</th><th>Precio</th><th>Categoría</th><th>Tipo</th><th></th></tr></thead>
      <tbody>
        <tr v-for="p in list" :key="p.id">
          <td>{{ p.name }}</td><td>\${{ p.price }}</td><td>{{ catMap[p.category_id] ?? p.category_id }}</td><td>{{ p.product_type }} {{ p.pote_size ?? '' }}</td>
          <td class="text-right"><v-btn size="small" variant="text" @click="openEdit(p as never)">Editar</v-btn><v-btn size="small" variant="text" color="error" @click="remove(p.id)">Eliminar</v-btn></td>
        </tr>
      </tbody>
    </v-table>
    <v-dialog v-model="dlg" max-width="560">
      <v-card :title="editing ? 'Editar producto' : 'Nuevo producto'">
        <v-card-text>
          <v-text-field v-model="form.name" label="Descripción *" :rules="[rRequired]" :error-messages="fieldErr('name')" density="compact" placeholder="Pote 1kg" />
          <v-text-field v-model="form.price" label="Precio *" prefix="$" type="number" :rules="[rRequired,rPrice]" :error-messages="fieldErr('price')" density="compact" />
          <v-select v-model="form.category_id" :items="catItems" label="Categoría *" :rules="[rRequired]" :error-messages="fieldErr('category_id')" density="compact" />
          <v-select v-model="form.product_type" :items="types" label="Tipo" density="compact" />
          <v-select v-if="form.product_type==='POTE'" v-model="form.pote_size" :items="sizes" label="Pote size" density="compact" />
          <v-row v-if="form.product_type==='POTE'">
            <v-col cols="6"><v-text-field v-model.number="form.min_flavors" label="Min gustos" type="number" :hint="autoHint" persistent-hint density="compact" /></v-col>
            <v-col cols="6"><v-text-field v-model.number="form.max_flavors" label="Cant. Gustos (máx)" type="number" :error-messages="maxErr||fieldErr('max_flavors')" :hint="hint" persistent-hint density="compact" /></v-col>
          </v-row>
          <div v-if="form.product_type==='POTE'" class="mt-2">
            <div class="text-subtitle-2 mb-1">Gustos disponibles (opcional)</div>
            <div class="text-caption text-medium-emphasis mb-2">Vacío = todos los gustos.</div>
            <v-checkbox v-for="f in flavors" :key="f.id" v-model="form.flavor_ids" :label="f.name" :value="f.id" density="compact" hide-details />
          </div>
          <v-alert v-if="formError" type="error" density="compact" class="mt-2">{{ formError }}</v-alert>
        </v-card-text>
        <v-card-actions><v-spacer/><v-btn variant="text" @click="dlg=false">Cancelar</v-btn><v-btn color="primary" :loading="saving" :disabled="!!maxErr" @click="save">Guardar</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>
<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useAdminCategories, useAdminProducts, useCreateProduct, useUpdateProduct, useDeleteProduct, errDetails } from '@/composables/useAdminCatalog'
import { qk } from '@/queries/keys'
import { api } from '@/api/client'
import { bounds } from '@/utils/flavorPolicy'
const { data: cats } = useAdminCategories()
const catItems = computed(()=>((cats.value as {id:number;name:string}[])??[]).map(c=>({ title:c.name, value:c.id })))
const catMap = computed(()=>Object.fromEntries(((cats.value as {id:number;name:string}[])??[]).map(c=>[c.id,c.name])) as Record<number,string>)
const fltCat = ref<number|undefined>(undefined); const search = ref('')
const qkRef = computed(()=> qk.adminProducts({ category: fltCat.value, search: search.value || undefined }))
const { data, isLoading } = useAdminProducts(fltCat as never, search as never)
const list = computed(()=>(data.value as {id:number;name:string;price:string;category_id:number;product_type:string;pote_size:string|null}[])??[])
const flavors = ref<{id:number;name:string}[]>([])
async function loadFlavors(){ try{ const {data:d}=await api.get('/public/ice-zone/flavors/'); flavors.value=Array.isArray(d)?d:(d.results??[]) } catch{ try{ const {data:d}=await api.get('/catalog/flavors/'); flavors.value=Array.isArray(d)?d:(d.results??[]) } catch{ flavors.value=[] } } }
loadFlavors()
const dlg=ref(false); const editing=ref<number|null>(null); const saving=ref(false)
const form=reactive({ name:'', price: '' as string|number, category_id: null as number|null, product_type:'POTE' as 'POTE'|'UNIT', pote_size:'KG_1' as 'KG_1'|'KG_HALF'|'KG_QUARTER'|null, min_flavors:1, max_flavors:4, flavor_ids: [] as number[] })
const details=ref<Record<string,string>>({}); const formError=ref('')
const fieldErr=(k:string)=>details.value[k]??''
const rRequired=(v:unknown)=>!!v||'Requerido'
const rPrice=(v:unknown)=>Number(v)>0||'>0'
const types=[{title:'POTE',value:'POTE'},{title:'UNIT',value:'UNIT'}]
const sizes=[{title:'1kg',value:'KG_1'},{title:'1/2kg',value:'KG_HALF'},{title:'1/4kg',value:'KG_QUARTER'}]
const hint=computed(()=>{ const b=bounds(form.pote_size, form.product_type); if(!b.max) return ''; return `Permitido ${b.min} a ${b.max} gustos` })
const autoHint=computed(()=>`Auto ${bounds(form.pote_size,'POTE').min} según tamaño (editable)`)
const maxErr=computed(()=>{
  if(form.product_type!=='POTE') return ''
  const b=bounds(form.pote_size,'POTE')
  if(form.min_flavors<1||form.min_flavors>4) return 'min 1-4'
  if(form.max_flavors<1||form.max_flavors>4) return `BR-CAT-04/05: para ${form.pote_size} permitido ${b.min}-${b.max} (máx 4)`
  if(form.min_flavors>form.max_flavors) return 'min no puede > max'
  if(form.max_flavors<b.min||form.max_flavors>b.max) return `BR-CAT-04/05: para ${form.pote_size} permitido ${b.min}-${b.max}`
  if(form.min_flavors<b.min) return `min debe ser >= ${b.min}`
  return ''
})
watch(()=>form.pote_size,(ns)=>{ const b=bounds(ns,'POTE'); if(form.min_flavors<b.min) form.min_flavors=b.min; if(form.max_flavors<b.min||form.max_flavors>b.max) form.max_flavors=b.max })
const createM=useCreateProduct(qkRef.value as never); const updateM=useUpdateProduct(qkRef.value as never); const deleteM=useDeleteProduct(qkRef.value as never)
function openCreate(){ editing.value=null; Object.assign(form,{ name:'Pote 1kg', price:'', category_id: (cats.value as {id:number}[]|undefined)?.[0]?.id ?? null, product_type:'POTE', pote_size:'KG_1', min_flavors:1, max_flavors:4, flavor_ids:[] }); details.value={}; formError.value=''; dlg.value=true }
function openEdit(p: {id:number;name:string;price:string;category_id:number;product_type:'POTE'|'UNIT';pote_size:'KG_1'|'KG_HALF'|'KG_QUARTER'|null;min_flavors:number|null;max_flavors:number|null}){ editing.value=p.id; Object.assign(form,{ name:p.name, price:p.price, category_id:p.category_id, product_type:p.product_type, pote_size:p.pote_size, min_flavors:p.min_flavors??1, max_flavors:p.max_flavors??4, flavor_ids:[] }); details.value={}; formError.value=''; dlg.value=true }
async function save(){
  if(maxErr.value){ formError.value=maxErr.value; return }
  if(!String(form.name).trim()||!form.price||!form.category_id){ details.value={ ...(!String(form.name).trim()?{name:'Requerido'}:{}), ...(!form.price?{price:'Requerido'}:{}), ...(!form.category_id?{category_id:'Requerido'}:{}) }; return }
  saving.value=true; details.value={}; formError.value=''
  const payload: Record<string,unknown>={ name:form.name, price:String(form.price), category_id:form.category_id, product_type:form.product_type }
  if(form.product_type==='POTE'){ Object.assign(payload,{ pote_size:form.pote_size, min_flavors:form.min_flavors, max_flavors:form.max_flavors, flavor_ids: form.flavor_ids }) }
  try{ if(editing.value) await updateM.mutateAsync({ id:editing.value, ...payload } as never); else await createM.mutateAsync(payload as never); dlg.value=false }
  catch(e: unknown){ const d=errDetails(e); if(Object.keys(d).length) details.value=d as Record<string,string>; else formError.value=(e as {response?:{data?:unknown}})?.response?.data ? JSON.stringify((e as {response:{data:unknown}}).response.data) : 'Error al guardar' }
  finally{ saving.value=false }
}
async function remove(id:number){ if(!confirm('¿Eliminar producto?')) return; try{ await deleteM.mutateAsync(id as never) } catch{ alert('Error al eliminar') } }
</script>
