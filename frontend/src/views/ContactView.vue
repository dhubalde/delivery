<template>
  <v-container max-width="900">
    <h2 class="mb-2" style="font-family: Comfortaa">Contacto</h2>
    <p class="text-body-2 text-medium-emphasis mb-4">
      ¿Necesitas ayuda? Dejanos tu mensaje — futuro bot/formulario en caso de
      error.
    </p>
    <v-card class="contact-form">
      <v-card-text>
        <v-form @submit.prevent="submit">
          <v-text-field
            v-model="form.name"
            label="Nombre"
            density="compact"
            :rules="[required]"
          />
          <v-text-field
            v-model="form.email"
            label="Email"
            density="compact"
            type="email"
            :rules="[required, emailRule]"
          />
          <v-textarea
            v-model="form.message"
            label="Mensaje"
            density="compact"
            rows="4"
            :rules="[required]"
          />
          <v-alert v-if="error" type="error" density="compact" class="mb-3">{{
            error
          }}</v-alert>
          <v-alert
            v-if="success"
            type="success"
            density="compact"
            class="mb-3"
            >{{ success }}</v-alert
          >
          <v-btn type="submit" color="primary" :loading="sending">Enviar</v-btn>
        </v-form>
      </v-card-text>
    </v-card>
    <FooterContact />
  </v-container>
</template>
<script setup lang="ts">
  import { reactive, ref } from "vue";
  import FooterContact from "@/components/FooterContact.vue";

  const form = reactive({ name: "", email: "", message: "" });
  const error = ref("");
  const success = ref("");
  const sending = ref(false);

  function required(v: string) {
    return !!v || "Requerido";
  }
  function emailRule(v: string) {
    return /.+@.+/.test(v) || "Email inválido";
  }

  async function submit() {
    error.value = "";
    success.value = "";
    if (!form.name || !form.email || !form.message) {
      error.value = "Completá todos los campos";
      return;
    }
    if (!/.+@.+/.test(form.email)) {
      error.value = "Email inválido";
      return;
    }
    sending.value = true;
    await new Promise((r) => setTimeout(r, 600));
    sending.value = false;
    success.value =
      "Mensaje enviado — placeholder, futuro bot/formulario de error.";
    form.name = "";
    form.email = "";
    form.message = "";
  }
</script>
<style scoped>
  .contact-form {
    max-width: 600px;
    margin: 0 auto;
  }
</style>
