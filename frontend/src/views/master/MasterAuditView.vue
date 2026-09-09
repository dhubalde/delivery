<template>
  <v-container fluid class="pa-4">
    <h2 class="text-h6 mb-2">Auditoría</h2>
    <v-card>
      <v-list v-if="list.length" lines="two">
        <v-list-item v-for="e in list" :key="e.id"
          :title="`${e.action} — ${e.actor ?? 'sistema'}`"
          :subtitle="`${e.merchant ?? 'plataforma'} · ${new Date(e.created_at).toLocaleString('es-AR')}`" />
      </v-list>
      <v-card-text v-else class="text-medium-emphasis">Sin movimientos.</v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMasterAudit } from '@/composables/useMaster'

const { data } = useMasterAudit()
const list = computed(() => data.value ?? [])
</script>
