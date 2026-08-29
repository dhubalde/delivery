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
const needsFlavors = computed(()=> props.p.product_type==='POTE' && !!props.p.pote_size)
const hint = computed(()=> needsFlavors.value ? phint(props.p.pote_size, props.p.product_type) : '')
const err = computed(()=> needsFlavors.value ? validate(props.p.pote_size, props.p.product_type, sel.value.length) : null)
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
