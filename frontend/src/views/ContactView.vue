<template>
  <v-container max-width="600">
    <h2 class="mb-2" style="font-family:Comfortaa">Contacto</h2>
    <p class="text-body-2 text-medium-emphasis mb-4">¿Necesitas ayuda? Dejanos tu mensaje — futuro bot/formulario en caso de error.</p>
    <v-card>
      <v-card-text>
        <v-form @submit.prevent="submit">
          <v-text-field v-model="form.name" label="Nombre" density="compact" :rules="[required]" />
          <v-text-field v-model="form.email" label="Email" density="compact" type="email" :rules="[required, emailRule]" />
          <v-textarea v-model="form.message" label="Mensaje" density="compact" rows="4" :rules="[required]" />
          <v-alert v-if="error" type="error" density="compact" class="mb-3">{{ error }}</v-alert>
          <v-alert v-if="success" type="success" density="compact" class="mb-3">{{ success }}</v-alert>
          <v-btn type="submit" color="primary" :loading="sending">Enviar</v-btn>
        </v-form>
      </v-card-text>
    </v-card>
    <v-card variant="tonal" rounded="lg" class="mt-4 pa-4 contact-company-footer">
      <div class="text-subtitle-2 font-weight-bold d-flex align-center ga-2">
        <v-icon size="18">mdi-domain</v-icon>
        <span>Empresa Tecnológica</span>
      </div>
      <v-divider class="my-3" />
      <div class="d-flex flex-column ga-2 text-body-2">
        <div class="d-flex align-center ga-2">
          <v-icon size="16">mdi-phone</v-icon>
          <span>Tel: +54 11 5555-0000</span>
        </div>
        <div class="d-flex align-center ga-2">
          <v-icon size="16">mdi-email-outline</v-icon>
          <span>soporte@empresatec.com</span>
        </div>
        <div class="d-flex align-center ga-2">
          <v-icon size="16">mdi-map-marker-outline</v-icon>
          <span>Av. Tecnológica 1234, CABA, Argentina</span>
        </div>
      </div>
      <v-divider class="my-3" />
      <div class="d-flex align-center ga-2">
        <span class="text-caption text-medium-emphasis">Redes:</span>
        <v-btn icon="mdi-instagram" variant="text" size="small" density="comfortable" aria-label="Instagram placeholder" />
        <v-btn icon="mdi-linkedin" variant="text" size="small" density="comfortable" aria-label="LinkedIn placeholder" />
        <v-btn icon="mdi-web" variant="text" size="small" density="comfortable" aria-label="Sitio web placeholder" />
        <span class="text-caption text-disabled">placeholder redes</span>
      </div>
    </v-card>
  </v-container>
</template>
<script setup lang="ts">
import { reactive, ref } from 'vue'

const form = reactive({ name: '', email: '', message: '' })
const error = ref('')
const success = ref('')
const sending = ref(false)

function required(v: string) { return !!v || 'Requerido' }
function emailRule(v: string) { return /.+@.+/.test(v) || 'Email inválido' }

async function submit() {
  error.value = ''
  success.value = ''
  if (!form.name || !form.email || !form.message) { error.value = 'Completá todos los campos'; return }
  if (!/.+@.+/.test(form.email)) { error.value = 'Email inválido'; return }
  sending.value = true
  await new Promise((r) => setTimeout(r, 600))
  sending.value = false
  success.value = 'Mensaje enviado — placeholder, futuro bot/formulario de error.'
  form.name = ''
  form.email = ''
  form.message = ''
}
</script>
