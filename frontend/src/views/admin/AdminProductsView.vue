<template>
  <v-container>
    <div class="d-flex align-center justify-space-between mb-1 flex-wrap ga-2">
      <div>
        <h2 class="text-h6" style="font-family:Comfortaa">Productos</h2>
        <div class="text-caption text-medium-emphasis">Catálogo — precios, gustos y fotos</div>
      </div>
      <v-btn color="primary" density="compact" prepend-icon="mdi-plus" :disabled="!isAdmin" @click="openCreate">Nuevo</v-btn>
    </div>
    <v-alert v-if="!isAdmin" type="warning" class="mb-4">Solo ADMIN puede editar productos</v-alert>
    <v-card variant="tonal" class="mb-3">
      <v-card-text class="d-flex flex-wrap ga-2 align-center py-2">
        <v-text-field v-model="search" label="Buscar" prepend-inner-icon="mdi-magnify" clearable density="compact" hide-details style="max-width:260px" />
        <v-select v-model="fltCat" :items="catItems" label="Categoría" clearable density="compact" hide-details style="max-width:220px" />
      </v-card-text>
    </v-card>
    <v-alert v-if="isForbidden" type="error" class="mb-2">403 — ADMIN requerido</v-alert>
    <v-skeleton-loader v-if="isLoading" type="list-item@3" />
<v-alert v-else-if="!list.length" type="info">Sin productos — ajustá filtros o creá uno</v-alert>
      <v-table density="compact" fixed-header hover>
        <thead>
          <tr><th>Nombre</th><th>Tipo</th><th>Precio</th><th>Gustos</th><th class="text-right">Acciones</th></tr>
        </thead>
        <tbody>
          <tr v-for="p in list" :key="p.id">
            <td>
              <span class="font-weight-medium">{{ p.name }}</span>
              <span v-if="p.description" class="ml-2 text-caption text-medium-emphasis"><v-icon size="12" color="primary">mdi-text</v-icon>{{ p.description.length>40 ? p.description.slice(0,40)+'…' : p.description }}</span>
            </td>
            <td class="text-medium-emphasis">{{ p.product_type }}{{ p.pote_size ? ' (' + p.pote_size.replace('KG_1','1kg').replace('KG_HALF','1/2kg').replace('KG_QUARTER','1/4kg') + ')' : '' }}</td>
            <td>${{ p.price }}</td>
            <td class="text-caption text-medium-emphasis">{{ flavorHint(p) }}</td>
            <td class="text-right text-no-wrap">
              <v-btn icon="mdi-pencil" size="small" density="compact" variant="text" title="Editar" :disabled="!isAdmin" @click="openEdit(p as never)" />
              <v-btn icon="mdi-delete" size="small" density="compact" variant="text" color="error" title="Eliminar" :disabled="!isAdmin" @click="remove(p.id)" />
            </td>
          </tr>
        </tbody>
      </v-table>
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
          <v-checkbox v-model="form.has_description" label="Agregar descripción corta" density="compact" hide-details />
          <v-textarea v-if="form.has_description" v-model="form.description" label="Descripción corta" :counter="160" maxlength="160" rows="2" auto-grow density="compact" hint="Ideal para deco/juguetes - máx 160 caracteres" persistent-hint :error-messages="fieldErr('description')" />
          <v-file-input v-model="form.imageFile" label="Foto (archivo)" accept="image/*" density="compact" clearable prepend-icon="" :error-messages="fieldErr('image')" hint="Subí una foto propia (JPG/PNG). Si no elegís archivo, se usa la URL." persistent-hint @update:model-value="onFileChange" />
          <v-text-field v-model="form.image_url" label="Imagen URL (fallback)" placeholder="https://..." density="compact" clearable :error-messages="fieldErr('image_url')" hint="URL alternativa si no subís archivo" persistent-hint />
          <v-img v-if="previewSrc" :src="previewSrc" height="120" cover class="mt-2 rounded" style="border:1px solid #eee" />
          <v-alert v-if="poteHint" type="info" density="compact" class="mt-2">{{ poteHint }}</v-alert>
          <v-alert v-if="formError" type="error" density="compact" class="mt-2">{{ formError }}</v-alert>
        </v-card-text>
        <v-card-actions><v-spacer/><v-btn variant="text" density="compact" @click="dlg=false">Cancelar</v-btn><v-btn color="primary" density="compact" :loading="saving" :disabled="!isAdmin" @click="save">Guardar</v-btn></v-card-actions>
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
import { catalogApi } from '@/api/panel/catalog.api'
import { useQueryClient } from '@tanstack/vue-query'
const auth = useAuthStore(); const isAdmin = computed(()=>hasAnyRole(auth.roles,['ADMIN']))
const { data: cats } = useAdminCategories()
const catItems = computed(()=>((cats.value as {id:number;name:string}[])??[]).map(c=>({ title:c.name, value:c.id })))
const poteSizeItems = [{ title: '1 kg', value: 'KG_1' }, { title: '1/2 kg', value: 'KG_HALF' }, { title: '1/4 kg', value: 'KG_QUARTER' }]
const fltCat = ref<number|undefined>(undefined); const search = ref('')
const qkRef = computed(()=> qk.adminProducts({ category: fltCat.value, search: search.value || undefined }))
const { data, isLoading, error } = useAdminProducts(fltCat as never, search as never)
const list = computed(()=>(data.value as {id:number;name:string;description?:string|null;product_type:string;pote_size:string|null;price:string;min_flavors:number|null;max_flavors:number|null}[])??[])
function flavorHint(p: {min_flavors:number|null;max_flavors:number|null}): string { if(p.min_flavors==null||p.max_flavors==null) return 'sin gustos'; return p.min_flavors===p.max_flavors ? `${p.min_flavors} gustos` : `${p.min_flavors} a ${p.max_flavors} gustos` }
const isForbidden = computed(()=>(error.value as { response?:{status?:number}})?.response?.status===403)
const dlg=ref(false); const editing=ref<number|null>(null); const saving=ref(false)
const form=reactive({ name:'', category_id: null as number|null, product_type:'POTE' as 'POTE'|'UNIT', pote_size:'KG_1' as 'KG_1'|'KG_HALF'|'KG_QUARTER'|null, has_flavors:true, min_flavors:1 as number|null, max_flavors:4 as number|null, price:'' , image_url:'' as string, imageFile: null as File | File[] | null, has_description:false as boolean, description:'' as string })
const filePreview = ref<string | null>(null)
const previewSrc = computed(()=> filePreview.value || form.image_url || null)
function onFileChange(v: File | File[] | null){ const f = Array.isArray(v) ? v[0] ?? null : v; if(f){ if(filePreview.value) URL.revokeObjectURL(filePreview.value); filePreview.value = URL.createObjectURL(f); form.imageFile = f as unknown as File; form.image_url = '' /* Clear image_url when new file is selected */ } else { if(filePreview.value) URL.revokeObjectURL(filePreview.value); filePreview.value = null; form.imageFile = null; } }
const details=ref<Record<string,string>>({}); const formError=ref('')
function fieldErr(k: string): string { return details.value[k] }
const poteHint=computed(()=> form.has_flavors ? hint(form.pote_size, form.product_type) : '')
const qc = useQueryClient()
const createM=useCreateProduct(qkRef.value as never); const updateM=useUpdateProduct(qkRef.value as never); const deleteM=useDeleteProduct(qkRef.value as never)
watch(()=>form.has_flavors, (v)=>{ if(v && (form.min_flavors==null || form.max_flavors==null)){ if(form.pote_size==='KG_QUARTER'){ form.min_flavors=1; form.max_flavors=3 } else { form.min_flavors=1; form.max_flavors=4 } } })
watch(()=>form.pote_size, (v)=>{ if(!form.has_flavors) return; if(v==='KG_QUARTER' && form.min_flavors===3 && form.max_flavors===4){ form.min_flavors=1; form.max_flavors=3 } })
watch(()=>form.product_type, (v)=>{ if(v==='UNIT'){ form.pote_size=null } else if(v==='POTE' && !form.pote_size){ form.pote_size='KG_1' } })
watch(()=>form.has_description, (v)=>{ if(!v) form.description='' })
function openCreate(){ editing.value=null; if(filePreview.value) URL.revokeObjectURL(filePreview.value); filePreview.value=null; Object.assign(form,{ name:'', category_id:null, product_type:'POTE', pote_size:'KG_1', has_flavors:true, min_flavors:1, max_flavors:4, price:'', image_url:'', imageFile:null, has_description:false, description:'' }); details.value={}; formError.value=''; dlg.value=true }
function openEdit(p: {id:number;name:string;category_id:number;product_type:'POTE'|'UNIT';pote_size:'KG_1'|'KG_HALF'|'KG_QUARTER'|null;min_flavors:number|null;max_flavors:number|null;price:string;image_url?:string|null;description?:string|null}){ const has = p.min_flavors!=null && p.max_flavors!=null; editing.value=p.id; if(filePreview.value) URL.revokeObjectURL(filePreview.value); filePreview.value=null; Object.assign(form,{ name:p.name, category_id:p.category_id, product_type:p.product_type, pote_size:p.pote_size, has_flavors:has, min_flavors:p.min_flavors ?? 1, max_flavors:p.max_flavors ?? 4, price:p.price, image_url:p.image_url ?? '', imageFile:null, has_description:!!p.description, description:p.description || '' }); details.value={}; formError.value=''; dlg.value=true }
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
  if(form.has_description && form.description.trim().length>160){ details.value={...details.value, description:'Máx 160 caracteres'}; return }
  saving.value=true; details.value={}; formError.value=''
  const descriptionVal = form.has_description ? form.description.trim() : ''
  const file = Array.isArray(form.imageFile) ? (form.imageFile[0] ?? null) : (form.imageFile as File | null)
  if(file){
    const fd = new FormData()
    fd.append('name', form.name)
    fd.append('category_id', String(form.category_id))
    fd.append('product_type', form.product_type)
    if(form.product_type==='UNIT') fd.append('pote_size', '')
    else if(form.pote_size) fd.append('pote_size', form.pote_size)
    else fd.append('pote_size', '')
    if(form.has_flavors){ fd.append('min_flavors', String(form.min_flavors)); fd.append('max_flavors', String(form.max_flavors)) }
    else { fd.append('min_flavors', ''); fd.append('max_flavors', '') }
    fd.append('price', String(form.price))
    fd.append('description', descriptionVal)
    if(form.image_url?.trim()) fd.append('image_url', form.image_url.trim())
    else fd.append('image_url', '')
    fd.append('image', file)
    try{ if(editing.value) await catalogApi.products.update(editing.value, fd); else await catalogApi.products.create(fd); qc.invalidateQueries({ queryKey: qkRef.value as never }); dlg.value=false }
    catch(e: unknown){ const d=errDetails(e); if(Object.keys(d).length) details.value=d as Record<string,string>; else formError.value=(e as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? 'Error al guardar' }
    finally{ saving.value=false }
    return
  }
  const imageUrl = form.image_url?.trim() || ''; const payload: Record<string,unknown>={ name:form.name, category_id:form.category_id, product_type:form.product_type, pote_size: form.product_type==='UNIT'?null:form.pote_size, min_flavors: form.has_flavors?form.min_flavors:null, max_flavors: form.has_flavors?form.max_flavors:null, price:form.price, image_url: imageUrl, description: descriptionVal, ...(!file && !imageUrl ? {image: null} : {}) }
  try{ if(editing.value) await updateM.mutateAsync({ id:editing.value, ...payload } as never); else await createM.mutateAsync(payload as never); dlg.value=false }
  catch(e: unknown){ const d=errDetails(e); if(Object.keys(d).length) details.value=d as Record<string,string>; else formError.value=(e as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? 'Error al guardar' }
  finally{ saving.value=false }
}
const confirm=useConfirm()
async function remove(id:number){ if(!await confirm.ask({ title:'¿Eliminar producto?', message:'Esta acción no se puede deshacer.' })) return; try{ await deleteM.mutateAsync(id) } catch(e: unknown){ toast((e as {response?:{status?:number}})?.response?.status===403 ? '403 — Solo ADMIN' : 'Error al eliminar') } }
</script>
