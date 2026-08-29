<template>
  <v-card>
    <v-img :src="img" height="180" cover>
      <template #error>
        <div class="d-flex align-center justify-center fill-height bg-grey-lighten-4">
          <v-icon size="48" color="grey">mdi-image-off-outline</v-icon>
        </div>
      </template>
      <template #placeholder>
        <div class="d-flex align-center justify-center fill-height">
          <v-progress-circular indeterminate size="24" />
        </div>
      </template>
    </v-img>
    <v-card-title class="text-body-2" style="font-family:Comfortaa">{{ p.name }}</v-card-title>
    <v-card-text>
      <v-chip v-if="badge" size="x-small" color="primary" class="mr-1">{{ badge }}</v-chip>
      <span class="font-weight-bold">${{ p.price }}</span>
      <div v-if="needsFlavors" class="text-caption text-medium-emphasis mt-1">{{ hint }}</div>
      <div v-else-if="flavors.length" class="mt-2"><v-chip v-for="f in flavors" :key="String(f)" size="x-small" class="mr-1 mb-1">{{ f }}</v-chip></div>
    </v-card-text>
    <v-card-actions><v-btn size="small" color="primary" @click="onAddClick">Agregar</v-btn></v-card-actions>
  </v-card>

  <v-dialog v-model="dialog" max-width="480" scrollable>
    <v-card>
      <v-card-title class="d-flex align-center ga-2">{{ p.name }}<v-chip v-if="badge" size="x-small" color="primary">{{ badge }}</v-chip></v-card-title>
      <v-divider />
      <v-card-text>
        <v-text-field v-model="searchRaw" label="Buscar gusto" variant="outlined" density="compact" hide-details clearable prepend-inner-icon="mdi-magnify" class="mb-3" />
        <div class="text-caption mb-2" :class="err ? 'text-error' : 'text-medium-emphasis'">{{ err || hint }} — Elegidos {{ sel.length }}/{{ max }}</div>
        <div style="max-height:300px;overflow-y:auto">
          <v-checkbox v-for="f in filtered" :key="String(f.id)" v-model="sel" :value="f.id" :label="f.name" density="compact" hide-details :disabled="!sel.includes(f.id) && sel.length >= max" />
          <div v-if="!filtered.length" class="text-caption text-medium-emphasis text-center py-4">Sin resultados</div>
        </div>
      </v-card-text>
      <v-divider />
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close">Cancelar</v-btn>
        <v-btn color="primary" :disabled="!!err" @click="confirm">Confirmar</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useCartStore } from '@/stores/cart.store'
import { boundsForProduct, hintForProduct, validateForProduct, bounds, hint as phint, validate } from '@/utils/flavorPolicy'
const props = defineProps<{ p: any }>()
const cart = useCartStore()
const sel = ref<any[]>([])
const dialog = ref(false)
const searchRaw = ref('')
const debounced = ref('')
let tid: ReturnType<typeof setTimeout> | null = null
watch(searchRaw, (v) => {
  if (tid) clearTimeout(tid)
  tid = setTimeout(() => { debounced.value = (v ?? '').trim().toLowerCase() }, 250)
})
const badge = computed(() => ({ KG_1:'1KG', KG_HALF:'1/2KG', KG_QUARTER:'1/4KG' } as Record<string,string>)[props.p.pote_size] ?? null)
const flavors = computed(() => (props.p.flavors ?? props.p.flavor_names ?? []) as any[])
const options = computed(() => {
  const f = props.p.flavors ?? props.p.flavor_names ?? ['Frutilla','Chocolate','Vainilla']
  return (f as any[]).map((x:any)=> typeof x==='string'? { id:x, name:x } : { id: x.id ?? x.name ?? x, name: x.name ?? String(x.id ?? x) })
})
const filtered = computed(() => {
  const q = debounced.value
  if (!q) return options.value
  return options.value.filter((o:any)=> String(o.name).toLowerCase().includes(q))
})
const needsFlavors = computed(()=> props.p.product_type==='POTE' && !!props.p.pote_size)
const hint = computed(()=> needsFlavors.value ? hintForProduct(props.p) : '')
const max = computed(()=> boundsForProduct(props.p).max)
const err = computed(()=> needsFlavors.value ? validateForProduct(props.p, sel.value.length) : null)
const img = computed(() => props.p.image_url || `/placeholders/${pick()}.jpg`)
function pick(){ const m:Record<string,string>={ KG_1:'pote-1kg', KG_HALF:'pote-medio', KG_QUARTER:'pote-cuarto' }; return m[props.p.pote_size] ?? 'pote-1kg' }
function onAddClick(){
  if (!needsFlavors.value) { cart.add(props.p, [], []); return }
  dialog.value = true
}
function close(){ dialog.value=false; sel.value=[]; searchRaw.value=''; debounced.value='' }
function confirm(){
  if (err.value) return
  const idList = sel.value.map((v:any)=> typeof v==='number'? v : 0).filter(Boolean)
  const fallbackIds: number[] = sel.value.map((_:any,i:number)=> i+1)
  const finalIds = idList.length ? idList : (sel.value as any[]).map((v:any)=> typeof v==='string'? v : String(v)) as any
  const nameList = options.value.filter((o:any)=> sel.value.includes(o.id)).map((o:any)=> o.name)
  cart.add(props.p, (finalIds.length? finalIds : fallbackIds) as any, nameList.length? nameList : sel.value as any)
  close()
}
watch(dialog, (v)=> { if(!v){ sel.value=[]; searchRaw.value=''; debounced.value='' } })
</script>
