<template>
  <v-card>
    <v-img :src="img" height="140" cover loading="lazy" />
    <v-card-title class="text-body-2" style="font-family:Comfortaa">{{ p.name }}</v-card-title>
    <v-card-text>
      <v-chip v-if="badge" size="x-small" color="primary" class="mr-1">{{ badge }}</v-chip>
      <span class="font-weight-bold">${{ p.price }}</span>
      <div v-if="needsFlavors" class="mt-2">
        <v-chip-group v-model="sel" multiple column>
          <v-chip v-for="f in options" :key="f.id ?? f" :value="f.id ?? f" size="x-small" filter>{{ f.name ?? f }}</v-chip>
        </v-chip-group>
        <div v-if="hint" class="text-caption" :class="err ? 'text-error' : 'text-medium-emphasis'">{{ err || hint }}</div>
      </div>
      <div v-else class="mt-2"><v-chip v-for="f in flavors" :key="f" size="x-small" class="mr-1 mb-1">{{ f }}</v-chip></div>
    </v-card-text>
    <v-card-actions><v-btn size="small" color="primary" :disabled="!!err || (needsFlavors && sel.length===0)" @click="add">Agregar</v-btn></v-card-actions>
  </v-card>
</template>
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useCartStore } from '@/stores/cart.store'
import { hint as phint, validate } from '@/utils/flavorPolicy'
const props = defineProps<{ p: any }>()
const cart = useCartStore()
const sel = ref<any[]>([])
const badge = computed(() => ({ KG_1:'1KG', KG_HALF:'1/2KG', KG_QUARTER:'1/4KG' } as Record<string,string>)[props.p.pote_size] ?? null)
const flavors = computed(() => props.p.flavors ?? props.p.flavor_names ?? [])
const options = computed(() => {
  const f = props.p.flavors ?? props.p.flavor_names ?? ['Frutilla','Chocolate','Vainilla']
  return f.map((x:any)=> typeof x==='string'? { id:x, name:x } : x)
})
const needsFlavors = computed(()=> {
  if (props.p.min_flavors==null || props.p.max_flavors==null) return false
  if (props.p.product_type==='POTE' && !!props.p.pote_size) return true
  return props.p.min_flavors!=null && props.p.max_flavors!=null
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
  if (props.p.min_flavors!=null && props.p.max_flavors!=null) {
    const n=sel.value.length
    if (n < props.p.min_flavors || n > props.p.max_flavors) return props.p.min_flavors===props.p.max_flavors ? `Elegí ${props.p.min_flavors} gustos` : `Elegí ${props.p.min_flavors} a ${props.p.max_flavors} gustos`
    return null
  }
  return validate(props.p.pote_size, props.p.product_type, sel.value.length)
})
const img = computed(() => props.p.image_url || `/placeholders/${pick()}.jpg`)
function pick(){ const m:Record<string,string>={ KG_1:'pote-1kg', KG_HALF:'pote-medio', KG_QUARTER:'pote-cuarto' }; return m[props.p.pote_size] ?? 'pote-1kg' }
function add(){
  const ids = sel.value.map((v:any)=> typeof v==='string'? v : v)
  const names = sel.value.map((v:any)=> typeof v==='string'? v : String(v))
  const flavorIds = ids.map((x:any)=> typeof x==='number'? x : 0).filter(Boolean)
  const idList = flavorIds.length? flavorIds : ids.map((_:any,i:number)=> i+1)
  const nameList = options.value.filter((o:any)=> sel.value.includes(o.id ?? o.name)).map((o:any)=> o.name ?? o)
  cart.add(props.p, idList.length? idList : sel.value as any, nameList.length? nameList : sel.value as any)
  sel.value=[]
}
</script>
