<template>
  <v-container>
    <ClosedBanner />
    <h2 class="text-h6 mb-4">Checkout</h2>
    <v-alert v-if="cart.isEmpty" type="info" variant="tonal">Carrito vacío</v-alert>
    <template v-else>
      <v-card class="pa-3 mb-3" v-for="it in cart.items" :key="it.uid">{{ it.product.name }} × {{ it.qty }} — ${{ it.product.price }}</v-card>
      <div class="font-weight-bold mb-2">Total: ${{ cart.total.toFixed(2) }}</div>
      <v-form @submit.prevent>
        <v-text-field v-model="customerName" label="Apellido y nombre *" density="compact" :error-messages="customerNameErr" class="mb-2" />
        <v-text-field v-model="customerPhone" label="Nº teléfono *" density="compact" :error-messages="customerPhoneErr" prefix="+54" hint="Sin 0 ni 15. 10 dígitos. Ej: 342 4508000 (Santa Fe) o 11 1234-5678 (CABA)" persistent-hint class="mb-2" type="tel" />
        <v-text-field v-model="address" label="Dirección de entrega *" density="compact" :error-messages="addressErr" hint="Ej: San Martín 1234, dpto 2B si corresponde" persistent-hint class="mb-1" />
        <div class="d-flex align-center ga-2 mb-2">
          <v-btn size="small" variant="tonal" prepend-icon="mdi-map-marker-check" @click="mapDialog = true">
            Confirmar en mapa
          </v-btn>
          <v-chip v-if="addressConfirmed" size="small" color="success" variant="tonal">
            <v-icon icon="mdi-check" start />Ubicación confirmada
          </v-chip>
        </div>
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
        <v-btn color="primary" block class="mt-3" :loading="loading" :disabled="closed" @click="submit">Confirmar pedido</v-btn>
      </v-form>
    </template>
    <v-snackbar v-model="ok" color="success">Pedido creado ¡Gracias!</v-snackbar>
    <v-dialog v-model="mapDialog" max-width="640" scrollable>
      <v-card>
        <v-card-title class="text-subtitle-1">Confirmá tu dirección en el mapa</v-card-title>
        <v-card-text>
          <AddressMapPicker
            :lat="addressGeo?.lat ?? null"
            :lng="addressGeo?.lng ?? null"
            :address-hint="address"
            @confirm="onMapConfirm"
            @cancel="mapDialog = false"
          />
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>
<script setup lang="ts">
import { parsePhoneNumberFromString } from 'libphonenumber-js'
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api } from '@/api/client'
import { useCartStore } from '@/stores/cart.store'
import { useMenu } from '@/composables/useMenu'
import { useCustomerStore } from '@/stores/customer.store'
import { addMyOrderIdForSlug, saveMyOrderSnapshot } from '@/composables/useMyOrders'
import ClosedBanner from '@/components/ClosedBanner.vue'
import AddressMapPicker, { type MapAddress } from '@/components/AddressMapPicker.vue'
const cart = useCartStore()
const customerStore = useCustomerStore()
const router = useRouter()
const route = useRoute()
const slug = computed(() => (route.params.slug as string) || 'ice-zone')
const methods = ['EFECTIVO','BILLETERA','TARJETA']
const payments = ref<{ method:string; amount:number }[]>([{ method:'EFECTIVO', amount: cart.total }])
const customerName = ref('')
const customerPhone = ref('')
const address = ref('')
const mapDialog = ref(false)
const addressGeo = ref<MapAddress | null>(null)
const addressConfirmed = computed(() => addressGeo.value !== null)

function geoKey(s: string): string {
  return `delivery:addr-geo:${s}`
}
function loadStoredGeo(s: string): void {
  try {
    const raw = localStorage.getItem(geoKey(s))
    if (!raw) return
    const parsed = JSON.parse(raw) as MapAddress
    if (typeof parsed.lat === 'number' && typeof parsed.lng === 'number') addressGeo.value = parsed
  } catch {
    /* ignore corrupt cache */
  }
}
function onMapConfirm(value: MapAddress): void {
  address.value = value.display_name
  addressGeo.value = value
  addressErr.value = ''
  try {
    localStorage.setItem(geoKey(slug.value), JSON.stringify(value))
  } catch {
    /* storage unavailable: geo still sent with the order */
  }
  mapDialog.value = false
}
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
function prefillFromProfile() {
  const p = customerStore.profile
  if (!p) return
  if (!customerName.value && p.name) customerName.value = p.name
  if (!customerPhone.value && p.phone) {
    try {
      const parsed = parsePhoneNumberFromString(p.phone, 'AR')
      customerPhone.value = parsed ? parsed.formatNational().replace(/^0/, '').replace(/(\s)15(\s|-)/, '$1') : p.phone
    } catch {
      customerPhone.value = p.phone
    }
  }
  if (!address.value && p.default_address) address.value = p.default_address
}
watch(
  slug,
  (s) => {
    cart.setSlug(s)
    customerStore.hydrate(s)
    loadStoredGeo(s)
    prefillFromProfile()
  },
  { immediate: true },
)
watch(address, (v) => {
  // Manual edits after a map confirmation invalidate the pinned location.
  if (addressGeo.value && v !== addressGeo.value.display_name) addressGeo.value = null
})
watch(
  () => cart.isEmpty,
  (empty) => {
    // Empty cart with no just-completed order means nothing to check out:
    // send the client back to the catalog instead of rendering an empty checkout.
    if (empty && !ok.value && !loading.value) router.replace(`/${slug.value}`)
  },
  { immediate: true },
)
const { data } = useMenu(slug as any) as any
const closed = computed(() => { const d=(data as any).value as any; return d ? (d.closed===true||d.is_open===false) : false })
const hasTarjeta = computed(() => payments.value.some((p) => p.method === 'TARJETA'))
const sumError = computed(() => {
  const s = payments.value.reduce((a,p)=>a+Number(p.amount||0),0)
  if (Math.abs(s - cart.total) > 0.01) return `Los montos deben sumar $${cart.total.toFixed(2)}`
  return null
})
function fieldErr(i:number){ return fieldErrs.value[i] || '' }
function validatePhone(): string {
  const raw = customerPhone.value.trim()
  if (!raw) return 'Requerido'
  const phone = parsePhoneNumberFromString(raw, 'AR')
  if (!phone || !phone.isValid()) return 'Teléfono inválido. Sin 0 ni 15. Ej: 342 4508000'
  return ''
}
async function submit(){
  if (loading.value) return
  inlineError.value=null; fieldErrs.value={}
  customerNameErr.value=''; customerPhoneErr.value=''; addressErr.value=''
  cardNumberErr.value=''; cardExpiryErr.value=''; cardCvvErr.value=''
  let hasErr=false
  if(!customerName.value.trim()){ customerNameErr.value='Requerido'; hasErr=true }
  const phoneErr = validatePhone()
  if (phoneErr) { customerPhoneErr.value = phoneErr; hasErr = true }
  if(!address.value.trim()){ addressErr.value='Requerido'; hasErr=true }
  else if(!/\d/.test(address.value)){ addressErr.value='Incluí altura/número. Ej: San Martín 1234'; hasErr=true }
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
    const currentSlug = slug.value
    const _parsed = parsePhoneNumberFromString(customerPhone.value, 'AR')
    const _e164 = _parsed && _parsed.isValid() ? _parsed.format('E.164') : customerPhone.value.trim()
    const body:any = { items: cart.items.map(i=>({ product_id:i.product.id, quantity:i.qty, flavor_ids:i.flavorIds })), payments: payments.value.map(p=>({ method:p.method, amount:String(p.amount) })), fulfillment: fulfillment.value, customer_name: customerName.value.trim(), customer_phone: _e164, address: address.value.trim() }
    // Extra geo fields are ignored gracefully by the public order endpoint
    // (it only reads known keys), and persist for future backend support.
    if (addressGeo.value) {
      body.address_lat = addressGeo.value.lat
      body.address_lng = addressGeo.value.lng
    }
    if(hasTarjeta.value){
      body.card = { number: cardNumber.value.replace(/\s/g,''), expiry: cardExpiry.value.trim(), cvv: cardCvv.value.trim() }
    }
    const { data: created } = await api.post(`/public/${currentSlug}/orders`, body, { headers: { 'Idempotency-Key': crypto.randomUUID() } }) as { data: { id: number; code: number; total: string } }
    if (created && typeof created.id === 'number') {
      addMyOrderIdForSlug(created.id, currentSlug)
      saveMyOrderSnapshot(currentSlug, { id: created.id, code: created.code, state: 'RECIBIDO', total: created.total, created_at: new Date().toISOString() })
    }
    cart.clear(); ok.value=true; setTimeout(()=>router.push(`/${currentSlug}/my-orders`), 800)
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
