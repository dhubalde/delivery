<template>
  <v-container>
    <h2 class="text-h6 mb-4">Admin Productos — Alta Pote</h2>
    <v-form @submit.prevent="submit" ref="formRef">
      <v-text-field v-model="form.name" label="Descripción" :rules="[rRequired]" placeholder="Pote 1kg" />
      <v-text-field v-model.number="form.price" label="Precio" type="number" :rules="[rRequired, rPrice]" prefix="$" />
      <v-select v-model="form.category_id" label="Categoría" :items="cats" item-title="name" item-value="id" :rules="[rRequired]" />
      <v-select v-model="form.product_type" label="Tipo" :items="types" />
      <v-select v-if="form.product_type==='POTE'" v-model="form.pote_size" label="Pote size" :items="sizes" />
      <v-row v-if="form.product_type==='POTE'">
        <v-col cols="6"><v-text-field v-model.number="form.min_flavors" label="Min gustos" type="number" :hint="autoHint" persistent-hint /></v-col>
        <v-col cols="6"><v-text-field v-model.number="form.max_flavors" label="Cant. Gustos (máx)" type="number" :error-messages="maxErr" :hint="hint" persistent-hint /></v-col>
      </v-row>
      <div v-if="form.product_type==='POTE'" class="mt-2">
        <div class="text-subtitle-2 mb-1">Gustos disponibles</div>
        <v-checkbox v-for="f in flavors" :key="f.id" v-model="form.flavor_ids" :label="f.name" :value="f.id" density="compact" hide-details />
        <div v-if="!flavors.length" class="text-caption text-medium-emphasis">Sin gustos — crea sabores en CRUD primero</div>
      </div>
      <v-alert v-if="error" type="error" class="mt-3" density="compact">{{ error }}</v-alert>
      <v-alert v-if="ok" type="success" class="mt-3" density="compact">Producto creado #{{ ok }}</v-alert>
      <v-btn type="submit" color="primary" class="mt-4" :loading="saving" :disabled="!!maxErr">Guardar</v-btn>
    </v-form>
  </v-container>
</template>
<script setup lang="ts">
import { computed, reactive, ref, watch, onMounted } from 'vue'
import { api } from '@/api/client'
import { useFlavors } from '@/composables/useProducts'
import { bounds } from '@/utils/flavorPolicy'
const slug = 'ice-zone'
const cats = ref<any[]>([])
const flavorsRef = useFlavors(slug as any, undefined as any, undefined as any) as any
const flavors = computed(() => (flavorsRef.data.value ?? []) as any[])
const form = reactive({ name: 'Pote 1kg', price: 12000 as number | null, category_id: null as number | null, product_type: 'POTE' as 'POTE'|'UNIT', pote_size: 'KG_1' as any, min_flavors: 3, max_flavors: 4, flavor_ids: [] as number[] })
const types = [{ title: 'POTE', value: 'POTE' }, { title: 'UNIT', value: 'UNIT' }]
const sizes = [{ title: '1kg', value: 'KG_1' }, { title: '1/2kg', value: 'KG_HALF' }, { title: '1/4kg', value: 'KG_QUARTER' }]
const rRequired = (v: any) => !!v || 'Requerido'
const rPrice = (v: any) => Number(v) > 0 || '>0'
const error = ref('')
const ok = ref<number | null>(null)
const saving = ref(false)
const formRef = ref()
const hint = computed(() => {
  const b = bounds(form.pote_size, form.product_type)
  if (!b.max) return ''
  return `Permitido ${b.min} a ${b.max} gustos`
})
const autoHint = computed(() => `Auto ${bounds(form.pote_size,'POTE').min} según tamaño (editable)`)
const maxErr = computed(() => {
  if (form.product_type !== 'POTE') return ''
  const b = bounds(form.pote_size, 'POTE')
  if (form.max_flavors < b.min || form.max_flavors > b.max) return `BR-CAT-04/05: para ${form.pote_size} permitido ${b.min}-${b.max}`
  if (form.min_flavors > form.max_flavors) return 'min no puede > max'
  if (form.min_flavors < b.min) return `min debe ser >= ${b.min}`
  return ''
})
watch(() => form.pote_size, (ns) => {
  const b = bounds(ns, 'POTE')
  form.min_flavors = b.min
  if (form.max_flavors < b.min || form.max_flavors > b.max) form.max_flavors = b.max
})
onMounted(async () => {
  try {
    const { data } = await api.get(`/public/${slug}/categories`)
    cats.value = Array.isArray(data) ? data : (data.results ?? [])
    if (cats.value.length && !form.category_id) form.category_id = cats.value[0].id
  } catch { const { data } = await api.get('/catalog/products/', { params: { merchant_slug: slug } }).catch(()=>({data:[]})) }
})
async function submit(){
  error.value=''; ok.value=null
  if (maxErr.value) { error.value = maxErr.value; return }
  saving.value=true
  try{
    const payload:any = { name: form.name, price: String(form.price), category_id: form.category_id, product_type: form.product_type }
    if (form.product_type==='POTE'){ payload.pote_size=form.pote_size; payload.min_flavors=form.min_flavors; payload.max_flavors=form.max_flavors; payload.flavor_ids=form.flavor_ids }
    const { data } = await api.post('/catalog/products/', payload)
    ok.value = data.id
  }catch(e:any){ error.value = e?.response?.data ? JSON.stringify(e.response.data) : e.message } finally{ saving.value=false }
}
</script>
