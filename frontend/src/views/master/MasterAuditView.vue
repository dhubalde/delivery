<template>
  <v-container fluid class="pa-4">
    <h2 class="text-h6 mb-2">Auditoría</h2>
    <DataTableCard
      v-model:search="search"
      :headers="headers"
      :items="list"
      :total="list.length"
      :search-keys="['action', 'actor', 'merchant']"
      search-label="Buscar acción, actor o empresa"
      no-data-text="Sin movimientos."
    >
      <template #item.action="{ item }">
        <span class="font-weight-medium">{{ item.action }}</span>
      </template>
      <template #item.actor="{ item }">
        <span class="text-medium-emphasis">{{ item.actor ?? 'sistema' }}</span>
      </template>
      <template #item.merchant="{ item }">
        <v-chip size="small" variant="tonal">{{ item.merchant ?? 'plataforma' }}</v-chip>
      </template>
      <template #item.created_at="{ item }">
        <span class="text-caption">{{ new Date(item.created_at).toLocaleString('es-AR') }}</span>
      </template>
    </DataTableCard>
  </v-container>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMasterAudit } from '@/composables/useMaster'
import DataTableCard from '@/components/DataTableCard.vue'

const { data } = useMasterAudit()
const list = computed(() => data.value ?? [])
const search = ref('')
const headers = [
  { title: 'Acción', key: 'action' },
  { title: 'Actor', key: 'actor' },
  { title: 'Empresa', key: 'merchant', align: 'center' as const },
  { title: 'Fecha', key: 'created_at', align: 'end' as const },
]
</script>
