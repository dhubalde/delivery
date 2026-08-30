<template>
  <v-card>
    <v-img :src="img" height="140" cover loading="lazy" />
    <v-card-title class="text-body-2" style="font-family:Comfortaa">{{ p.name }}</v-card-title>
    <v-card-text v-if="needsFlavors" class="pb-0">
      <div class="text-caption text-center text-medium-emphasis">{{ hint }}</div>
    </v-card-text>
    <v-card-actions class="d-flex align-center justify-space-between">
      <div class="d-flex align-center ga-2">
        <v-chip v-if="badge" size="x-small" color="primary">{{ badge }}</v-chip>
        <span class="font-weight-bold">${{ priceFormatted }}</span>
      </div>
      <v-tooltip text="Agregar al carrito" location="top">
        <template #activator="{ props: tProps }">
          <v-btn v-bind="tProps" icon size="small" color="primary" :disabled="!p.is_active" @click="onAddClick" aria-label="Agregar al carrito"><v-icon>mdi-plus</v-icon></v-btn>
        </template>
      </v-tooltip>
    </v-card-actions>
  </v-card>

  <v-dialog v-model="dialog" max-width="420">
    <v-card>
      <v-card-title class="text-body-1" style="font-family:Comfortaa">Elige tus gustos</v-card-title>
      <v-card-text>
        <div class="text-caption text-center" :class="err ? 'text-error' : 'text-medium-emphasis'">{{ err || hint }}</div>
        <v-chip-group v-model="selected" multiple column>
          <v-chip v-for="f in options" :key="f.id ?? f.name" :value="f.id ?? f.name" size="x-small" filter>{{ f.name }}</v-chip>
        </v-chip-group>
        <v-alert v-if="err" type="error" variant="tonal" density="compact" class="mt-2">{{ err }}</v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="closeDialog">Cancelar</v-btn>
        <v-btn color="primary" :disabled="!!err" @click="confirmAdd"><v-icon start>mdi-plus</v-icon>Agregar</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useCartStore } from '@/stores/cart.store'
import { useAuthStore } from '@/stores/auth.store'
import { useFlavors } from '@/composables/useProducts'
import { toast } from '@/composables/useConfirm'
const props = defineProps<{ p: any }>()
const cart = useCartStore()
const auth = useAuthStore()
const slug = computed(() => auth.merchantSlug || 'ice-zone')
const { data: flavorsData } = useFlavors(slug as any, computed(() => undefined), computed(() => undefined)) as any
const dialog = ref(false)
const selected = ref<any[]>([])
const badge = computed(() => ({ KG_1: '1 kg', KG_HALF: '1/2 kg', KG_QUARTER: '1/4 kg' } as Record<string, string>)[props.p.pote_size] ?? null)
const priceFormatted = computed(() => Number(props.p.price).toFixed(2))
const options = computed(() => {
  const pFlavors = props.p.flavors ?? props.p.flavor_names
  if (Array.isArray(pFlavors) && pFlavors.length) {
    return (pFlavors as any[]).map((x: any) => typeof x === 'string' ? { id: x, name: x } : { id: x.id ?? x.name, name: x.name ?? String(x) })
  }
  const fetched = (flavorsData.value as any[] | undefined) ?? []
  if (fetched.length) return fetched.map((x: any) => ({ id: x.id, name: x.name }))
  return [] as { id: any; name: string }[]
})
const needsFlavors = computed(() => {
  if (props.p.min_flavors == null || props.p.max_flavors == null) return false
  if (props.p.product_type === 'POTE' && !!props.p.pote_size) return true
  return props.p.min_flavors != null && props.p.max_flavors != null
})
const hint = computed(() => {
  if (!needsFlavors.value) return ''
  if (props.p.min_flavors != null && props.p.max_flavors != null) {
    return props.p.min_flavors === props.p.max_flavors ? `Elige ${props.p.min_flavors} gustos` : `Elige ${props.p.min_flavors} a ${props.p.max_flavors} gustos`
  }
  return ''
})
const err = computed(() => {
  if (!needsFlavors.value) return null
  return cart.canAdd(props.p, selected.value as number[])
})
const img = computed(() => props.p.image_url || `/placeholders/${pick()}.jpg`)
function pick() { const m: Record<string, string> = { KG_1: 'pote-1kg', KG_HALF: 'pote-medio', KG_QUARTER: 'pote-cuarto' }; return m[props.p.pote_size] ?? 'pote-1kg' }
function onAddClick() {
  if (!needsFlavors.value) {
    try {
      cart.add(props.p, [], [])
    } catch (e: any) {
      toast(e?.message ?? 'Error al agregar', 'error')
    }
    return
  }
  dialog.value = true
}
function closeDialog() {
  dialog.value = false
}
function confirmAdd() {
  const e = cart.canAdd(props.p, selected.value as number[])
  if (e) {
    toast(e, 'error')
    return
  }
  try {
    const flavorIds = selected.value.map((v: any, i: number) => typeof v === 'number' ? v : Number.isFinite(Number(v)) && String(v).trim() !== '' ? Number(v) : i + 1)
    const nameList = options.value.filter((o: any) => selected.value.includes(o.id ?? o.name)).map((o: any) => o.name ?? String(o))
    const flavorNames = nameList.length ? nameList : selected.value.map((v: any) => String(v))
    cart.add(props.p, flavorIds as any, flavorNames as any)
    selected.value = []
    dialog.value = false
  } catch (e: any) {
    toast(e?.message ?? 'Error al agregar', 'error')
  }
}
</script>
