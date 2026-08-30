<template>
  <v-container>
    <ClosedBanner />
    <h2 class="text-h6 mb-4">Checkout</h2>
    <v-alert v-if="cart.isEmpty" type="info" variant="tonal">Carrito vacío</v-alert>
    <template v-else>
      <v-card class="pa-3 mb-3" v-for="it in cart.items" :key="it.uid">{{ it.product.name }} × {{ it.qty }} — ${{ it.product.price }}</v-card>
      <div class="font-weight-bold mb-2">Total: ${{ cart.total.toFixed(2) }}</div>
      <v-form @submit.prevent="submit">
        <v-text-field v-model="customerName" label="Nombre y apellido *" density="compact" :error-messages="customerNameErr" class="mb-2" />
        <v-text-field v-model="customerPhone" label="Nº teléfono *" density="compact" :error-messages="customerPhoneErr" class="mb-2" />
        <v-text-field v-model="address" label="Dirección de entrega *" density="compact" :error-messages="addressErr" class="mb-2" />
        <v-select v-model="fulfillment" :items="['DELIVERY','PICKUP']" label="Entrega" density="compact" class="mb-2" style="max-width:200px" />
        <v-divider class="my-3" />
        <div class="text-subtitle-2 mb-2">Pagos</div>
        <div v-for="(pay, i) in payments" :key="i" class="d-flex ga-2 mb-2">
          <v-select v-model="pay.method" :items="methods" label="Método" density="compact" style="max-width:180px" />
          <v-text-field v-model.number="pay.amount" type="number" label="Monto" density="compact" :error-messages="fieldErr(i)" />
          <v-btn icon="mdi-delete" size="small" variant="text" @click="payments.splice(i,1)" v-if="payments.length>1" />
        </div>
        <v-btn size="small" variant="tonal" @click="payments.push({ method:'EFECTIVO', amount:0 })">Agregar pago</v-btn>
        <v-alert v-if="sumError" type="error" variant="tonal" class="mt-2">{{ sumError }}</v-alert>
        <template v-if="hasTarjeta">
          <v-divider class="my-3" />
          <div class="text-subtitle-2 mb-2">Datos de tarjeta (mock)</div>
          <v-text-field v-model="cardNumber" label="Número de tarjeta *" density="compact" :error-messages="cardNumberErr" placeholder="4111 1111 1111 1111" hint="Para probar usá 4111 1111 1111 1111" persistent-hint class="mb-2" />
          <div class="d-flex ga-2">
            <v-text-field v-model="cardExpiry" label="Vencimiento MM/AA *" density="compact" :error-messages="cardExpiryErr" placeholder="12/30" style="max-width:180px" />
            <v-text-field v-model="cardCvv" label="CVV *" density="compact" :error-messages="cardCvvErr" placeholder="123" style="max-width:120px" />
          </div>
        </template>
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
const customerName = ref('')
const customerPhone = ref('')
const address = ref('')
const fulfillment = ref('DELIVERY')
const cardNumber = ref('')
const cardExpiry = ref('')
const cardCvv = ref('')
const inlineError = ref<string|null>(null)
const fieldErrs = ref<Record<number,string>>({})
const loading = ref(false)
const ok = ref(false)
const customerNameErr = ref('')
const customerPhoneErr = ref('')
const addressErr = ref('')
const cardNumberErr = ref('')
const cardExpiryErr = ref('')
const cardCvvErr = ref('')
const { data } = useMenu(computed(() => auth.merchantSlug || 'zona-ice') as any) as any
const closed = computed(() => { const d=(data as any).value as any; return d ? (d.closed===true||d.is_open===false) : false })
const hasTarjeta = computed(() => payments.value.some((p) => p.method === 'TARJETA'))
const sumError = computed(() => {
  const s = payments.value.reduce((a,p)=>a+Number(p.amount||0),0)
  if (Math.abs(s - cart.total) > 0.01) return `Los montos deben sumar $${cart.total.toFixed(2)}`
  return null
})
function fieldErr(i:number){ return fieldErrs.value[i] || '' }
async function submit(){
  inlineError.value=null; fieldErrs.value={}
  customerNameErr.value=''; customerPhoneErr.value=''; addressErr.value=''
  cardNumberErr.value=''; cardExpiryErr.value=''; cardCvvErr.value=''
  let hasErr=false
  if(!customerName.value.trim()){ customerNameErr.value='Requerido'; hasErr=true }
  if(!customerPhone.value.trim()){ customerPhoneErr.value='Requerido'; hasErr=true }
  if(!address.value.trim()){ addressErr.value='Requerido'; hasErr=true }
  if(hasTarjeta.value){
    if(!cardNumber.value.trim()){ cardNumberErr.value='Requerido'; hasErr=true }
    else {
      const digits = cardNumber.value.replace(/\s/g,'')
      if(!/^\d+$/.test(digits)){ cardNumberErr.value='Solo números'; hasErr=true }
      else if(digits.length < 12 || digits.length > 19){ cardNumberErr.value='Debe tener 12 a 19 dígitos'; hasErr=true }
    }
    if(!cardExpiry.value.trim()){ cardExpiryErr.value='Requerido'; hasErr=true }
    else if(!/^\d{2}\/\d{2,4}$/.test(cardExpiry.value.trim())){ cardExpiryErr.value='Formato MM/AA o MM/AAAA'; hasErr=true }
    else {
      const [mm] = cardExpiry.value.trim().split('/')
      const m = Number(mm)
      if(m < 1 || m > 12){ cardExpiryErr.value='Mes inválido (01-12)'; hasErr=true }
    }
    if(!cardCvv.value.trim()){ cardCvvErr.value='Requerido'; hasErr=true }
    else if(!/^\d{3,4}$/.test(cardCvv.value.trim())){ cardCvvErr.value='CVV inválido'; hasErr=true }
  }
  if(hasErr) return
  if (sumError.value) { inlineError.value = sumError.value; return }
  loading.value=true
  try{
    const slug = auth.merchantSlug || 'zona-ice'
    const body:any = { items: cart.items.map(i=>({ product_id:i.product.id, quantity:i.qty, flavor_ids:i.flavorIds })), payments: payments.value.map(p=>({ method:p.method, amount:String(p.amount) })), fulfillment: fulfillment.value, customer_name: customerName.value.trim(), customer_phone: customerPhone.value.trim(), address: address.value.trim() }
    if(hasTarjeta.value){
      body.card = { number: cardNumber.value.replace(/\s/g,''), expiry: cardExpiry.value.trim(), cvv: cardCvv.value.trim() }
    }
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
