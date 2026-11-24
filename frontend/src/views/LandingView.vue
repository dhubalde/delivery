<template>
  <v-container class="landing" fluid>
    <v-card class="landing-card text-center pa-8" elevation="2" rounded="lg">
      <div class="landing-brand">
        <span>WORK</span><span class="landing-brand__zone">ZONE</span>
      </div>
      <p class="text-body-1 text-medium-emphasis mt-3 mb-6">
        Ingresá con el link de tu negocio.
      </p>
      <v-btn
        to="/login"
        color="primary"
        variant="tonal"
        density="compact"
        prepend-icon="mdi-account-key"
      >
        Soy del equipo
      </v-btn>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { brandColors } from '@/design'

// The root is intentionally merchant-neutral: the app serves several
// businesses, so no visitor may land in another company's catalog.
</script>

<style scoped>
.landing {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  padding: 24px;
}
.landing-card {
  width: 100%;
  max-width: 420px;
}
.landing-brand {
  font-family: Comfortaa, sans-serif;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.landing-brand__zone {
  color: v-bind('brandColors.primary');
  margin-left: 6px;
}
</style>
