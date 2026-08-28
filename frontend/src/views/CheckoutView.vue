<template>
  <v-container>
    <ClosedBanner />
    <h2 class="text-h6 mb-4">Checkout</h2>
    <v-alert v-if="cart.isEmpty" type="info" variant="tonal">Carrito vacío</v-alert>
    <template v-else>
      <v-card class="pa-3 mb-3" v-for="it in cart.items" :key="it.uid">{{ it.product.name }} × {{ it.qty }} — ${{ it.product.price }}</v-card>
      <div class="font-weight-bold mb-2">Total: ${{ cart.total.toFixed(2) }}</div>
      <v-form @submit.prevent="submit">
        <div v-for="(pay, i) in payments" :key="i" class="d-flex ga-2 mb-2">
          <v-select v-model="pay.method" :items="methods" label="Método" density="compact" style="max-width:180px" />
          <v-text-field v-model.number="pay.amount" type="number" label="Monto" density="compact" :error-messages="fieldErr(i)" />
          <v-btn icon="mdi-delete" size="small" variant="text" @click="payments.splice(i,1)" v-if="payments.length>1" />
        </div>
        <v-btn size="small" variant="tonal" @click="payments.push({ method:'EFECTIVO', amount:0 })">Agregar pago</v-btn>
        <v-alert v-if="sumError" type="error" variant="tonal" class="mt-2">{{ sumError }}</v-alert>
        <v-alert v-if="inlineError" type="error" variant="tonal" class="mt-2">{{ inlineError }}</v-alert>
        <v-btn type="submit" color="primary" block class="mt-3" :loading="loading" :disabled="closed">Confirmar pedido</v-btn>
      </v-form>
    </template>
    <v-snackbar v-model="ok" color="success">Pedido creado ¡Gracias!</v-snackbar>
  </v-container>
</template>
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useCartStore } from '@/stores/cart.store'
import { useMenu } from '@/composables/useMenu'
import { useAuthStore } from '@/stores/auth.store'
import ClosedBanner from '@/components/ClosedBanner.vue'
const cart = useCartStore()
const auth = useAuthStore()
const router = useRouter()
const methods = ['EFECTIVO','BILLETERA','TARJETA']
const payments = ref<{ method:string; amount:number }[]>([{ method:'EFECTIVO', amount: cart.total }])
const inlineError = ref<string|null>(null)
const fieldErrs = ref<Record<number,string>>({})
const loading = ref(false)
const ok = ref(false)
const { data } = useMenu(computed(() => auth.merchantSlug || 'zona-ice') as any) as any
const closed = computed(() => { const d=(data as any).value as any; return d ? (d.closed===true||d.is_open===false) : false })
const sumError = computed(() => {
  const s = payments.value.reduce((a,p)=>a+Number(p.amount||0),0)
  if (Math.abs(s - cart.total) > 0.01) return `Los montos deben sumar $${cart.total.toFixed(2)}`
  return null
})
function fieldErr(i:number){ return fieldErrs.value[i] || '' }
async function submit(){
  inlineError.value=null; fieldErrs.value={}
  if (sumError.value) { inlineError.value = sumError.value; return }
  loading.value=true
  try{
    const slug = auth.merchantSlug || 'zona-ice'
    const body = { items: cart.items.map(i=>({ product_id:i.product.id, quantity:i.qty, flavor_ids:i.flavorIds })), payments: payments.value.map(p=>({ method:p.method, amount:String(p.amount) })), fulfillment:'DELIVERY' }
    await api.post(`/public/${slug}/orders`, body, { headers: { 'Idempotency-Key': crypto.randomUUID() } })
    cart.clear(); ok.value=true; setTimeout(()=>router.push('/'), 800)
  }catch(e:any){
    const d=e?.response?.data
    const code=d?.error?.code
    if(code==='SCHEDULE_CLOSED') inlineError.value='Local cerrado'
    else if(code==='IDEMPOTENCY_KEY_REUSED') inlineError.value='Pedido duplicado'
    else if(e?.response?.status===400){ const det=d?.error?.details||d?.details; if(det){ Object.values(det).forEach((v:any,i)=>fieldErrs.value[i]=Array.isArray(v)?v[0]:String(v)); inlineError.value = typeof det==='string'?det : (det.payments?String(det.payments):'Revisá los datos') } else inlineError.value=d?.error?.message||'Error de validación' }
    else inlineError.value='Error inesperado, reintentar'
  }finally{ loading.value=false }
}
</script>
