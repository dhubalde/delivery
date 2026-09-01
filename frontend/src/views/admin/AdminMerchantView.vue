<template>
  <v-container>
    <h2 style="font-family:Comfortaa" class="mb-4">Empresa / Merchant</h2>
    <v-skeleton-loader v-if="loading" type="card" />
    <v-alert v-else-if="isError" type="error">No se pudo cargar el merchant</v-alert>
    <template v-else>
      <v-card class="mb-4">
        <v-card-text>
          <div class="d-flex align-center ga-4 mb-4 flex-wrap">
            <AppLogo :size="180" :force-default="false" />
            <div>
              <div class="text-h6" style="font-family:Comfortaa">{{ merchant?.name }}</div>
              <div class="text-caption text-medium-emphasis">slug: {{ merchant?.slug }} · vertical: {{ merchant?.vertical }}</div>
              <div class="text-caption">Logo actual: {{ merchant?.logo || merchant?.logo_url || 'default Ice Zone' }}</div>
            </div>
          </div>
          <v-divider class="mb-4" />
          <v-text-field v-model="form.logo_url" label="Logo URL (https://...)" density="compact" hint="Si subís archivo, este campo se ignora. Para multi-tenant: pega URL del logo de la empresa" persistent-hint :error-messages="details.logo_url ?? ''" />
          <v-file-input v-model="file" label="Subir logo (PNG/SVG/JPG)" accept="image/*" density="compact" class="mt-3" hint="Se guarda en /media/merchant_logos/" persistent-hint />
          <v-img v-if="previewUrl" :src="previewUrl" max-width="220" max-height="120" class="mt-3 border rounded" cover />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="resetForm">Cancelar</v-btn>
          <v-btn color="primary" :loading="saving" @click="save">Guardar</v-btn>
        </v-card-actions>
        <v-card-text v-if="formError"><v-alert type="error" density="compact">{{ formError }}</v-alert></v-card-text>
        <v-card-text v-if="formSuccess"><v-alert type="success" density="compact">{{ formSuccess }}</v-alert></v-card-text>
      </v-card>
      <v-alert type="info" variant="tonal">
        El logo se muestra automáticamente en <strong>AppLogo</strong>. Si el merchant tiene <code>logo</code> o <code>logo_url</code> configurado, se usa ese; si no, se usa el default minimalista Ice Zone (turquesa #06B6D4).
      </v-alert>
    </template>
  </v-container>
</template>
<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import AppLogo from '@/components/AppLogo.vue'
import { useMerchant, useUpdateMerchant } from '@/composables/useMerchant'
import { merchantApi } from '@/api/panel/merchant.api'

const { data, isLoading: loading, isError, refetch } = useMerchant()
const merchant = computed(() => data.value as unknown as { id:number; name:string; slug:string; vertical:string; logo:string|null; logo_url:string|null } | null)
const form = reactive({ logo_url: '' })
const details = ref<Record<string,string>>({})
const formError = ref('')
const formSuccess = ref('')
const file = ref<File[] | File | null>(null)
const saving = ref(false)

watch(() => merchant.value, (m) => { if (m) form.logo_url = m.logo_url || '' }, { immediate: true })

const previewUrl = computed(() => {
  const f = Array.isArray(file.value) ? file.value[0] : file.value as File | null
  if (f) return URL.createObjectURL(f)
  return merchant.value?.logo || merchant.value?.logo_url || null
})

const updateM = useUpdateMerchant()

function resetForm() {
  form.logo_url = merchant.value?.logo_url || ''
  file.value = null
  details.value = {}
  formError.value = ''
  formSuccess.value = ''
}

async function save() {
  saving.value = true
  details.value = {}
  formError.value = ''
  formSuccess.value = ''
  try {
    const f = Array.isArray(file.value) ? file.value[0] : file.value as File | null
    if (f) {
      await merchantApi.uploadLogo(f as File)
    } else {
      await updateM.mutateAsync({ logo_url: form.logo_url || null } as never)
    }
    await refetch()
    formSuccess.value = 'Logo actualizado'
    file.value = null
  } catch (e: unknown) {
    const d = (e as { response?: { data?: { error?: { details?: Record<string,string>; message?: string } } } })?.response?.data?.error?.details
    if (d && Object.keys(d).length) details.value = d as Record<string,string>
    else formError.value = (e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message ?? 'Error al guardar'
  } finally {
    saving.value = false
  }
}
</script>
