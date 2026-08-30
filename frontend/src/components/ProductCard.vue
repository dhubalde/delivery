<template>
  <v-list-item density="compact" class="px-2">
    <template #prepend>
      <v-avatar size="28" rounded="sm" class="mr-2"><v-img :src="img" cover /></v-avatar>
    </template>
    <div class="d-flex align-center ga-2 flex-wrap py-1 w-100" style="min-height:36px">
      <span class="text-body-2 font-weight-medium" style="font-family:Comfortaa">{{ p.name }}</span>
      <v-chip v-if="badge" size="x-small" color="primary">{{ badge }}</v-chip>
      <span class="text-caption text-medium-emphasis">{{ p.product_type }}</span>
      <span class="font-weight-bold text-body-2">${{ p.price }}</span>
      <template v-if="needsFlavors">
        <v-chip-group v-model="sel" multiple density="compact" column selected-class="text-primary" class="mx-1" style="max-width:420px">
          <v-chip v-for="f in options" :key="f.id ?? f" :value="f.id ?? f" size="x-small" filter density="compact">{{ f.name ?? f }}</v-chip>
        </v-chip-group>
        <span class="text-caption" :class="err ? 'text-error' : 'text-medium-emphasis'">{{ err || hint }}</span>
      </template>
      <template v-else>
        <span v-if="flavors.length" class="text-caption text-medium-emphasis">{{ flavors.join(', ') }}</span>
      </template>
      <v-spacer />
      <v-btn size="small" color="primary" density="compact" :disabled="!!err || (needsFlavors && sel.length===0)" @click="add">Agregar</v-btn>
    </div>
  </v-list-item>
  <v-divider />
</template>
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useCartStore } from '@/stores/cart.store'
import { hint as phint } from '@/utils/flavorPolicy'
const props = defineProps<{ p: any }>()
const cart = useCartStore()
const sel = ref<any[]>([])
const badge = computed(() => ({ KG_1:'1KG', KG_HALF:'1/2KG', KG_QUARTER:'1/4KG' } as Record<string,string>)[props.p.pote_size] ?? null)
const flavors = computed(() => props.p.flavors ?? props.p.flavor_names ?? [])
const FALLBACK = ['Chocolate','Vainilla','Frutilla','Dulce']
const options = computed(() => {
  const raw = (Array.isArray(props.p.flavors) && props.p.flavors.length ? props.p.flavors : Array.isArray(props.p.flavor_names) && props.p.flavor_names.length ? props.p.flavor_names : FALLBACK)
  return raw.map((x:any)=> typeof x==='string'? { id:x, name:x } : x)
})
const needsFlavors = computed(()=> {
  if (props.p.product_type==='POTE' && !!props.p.pote_size) return true
  if (props.p.min_flavors!=null && props.p.max_flavors!=null) return true
  return false
})
const hint = computed(()=> {
  if (!needsFlavors.value) return ''
  if (props.p.min_flavors!=null && props.p.max_flavors!=null) {
    return props.p.min_flavors===props.p.max_flavors ? `Elegí ${props.p.min_flavors} gustos` : `Elegí ${props.p.min_flavors} a ${props.p.max_flavors} gustos`
  }
  return phint(props.p.pote_size, props.p.product_type)
})
const err = computed(()=> {
  if (!needsFlavors.value) return null
  return cart.canAdd(props.p, sel.value as any)
})
const img = computed(() => props.p.image_url || `/placeholders/${pick()}.jpg`)
function pick(){ const m:Record<string,string>={ KG_1:'pote-1kg', KG_HALF:'pote-medio', KG_QUARTER:'pote-cuarto' }; return m[props.p.pote_size] ?? 'pote-1kg' }
function add(){
  const flavorIds = sel.value.map((v:any,i:number)=> typeof v==='number' ? v : Number.isFinite(Number(v)) && String(v).trim()!=='' ? Number(v) : i+1)
  const nameList = options.value.filter((o:any)=> sel.value.includes(o.id ?? o.name)).map((o:any)=> o.name ?? String(o))
  const flavorNames = nameList.length ? nameList : sel.value.map((v:any)=> String(v))
  cart.add(props.p, flavorIds as any, flavorNames as any)
  sel.value=[]
}
</script>
