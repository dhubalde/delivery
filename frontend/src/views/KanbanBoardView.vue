<template>
  <v-container fluid>
    <div class="d-flex justify-space-between align-center mb-4">
      <h2>Kanban — Ice Zone</h2>
      <v-text-field v-model="businessDate" type="date" density="compact" hide-details style="max-width: 180px" />
    </div>
    <v-row>
      <v-col v-for="col in cols" :key="col.state" cols="12" md="2">
        <KanbanColumn :title="col.title" :color="col.color" :orders="boards[col.state].data.value ?? []" :is-loading="boards[col.state].isLoading.value" :is-error="boards[col.state].isError.value" @retry="boards[col.state].refetch()" />
      </v-col>
      <v-col cols="12" md="2">
        <KanbanTotalsCard :fallback-orders="(boards['ENTREGADO'].data.value ?? []) as any" />
      </v-col>
    </v-row>
  </v-container>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { COLUMN_COLORS } from '@/theme/tokens'
import { useOrdersBoard } from '@/composables/useOrders'
import KanbanColumn from '@/components/KanbanColumn.vue'
import KanbanTotalsCard from '@/components/KanbanTotalsCard.vue'
const today = new Date().toISOString().slice(0, 10)
const businessDate = ref(today)
const cols = [
  { state: 'RECIBIDO', title: 'Recibido', color: COLUMN_COLORS.RECIBIDO },
  { state: 'PREPARACION', title: 'Preparación', color: COLUMN_COLORS.PREPARACION },
  { state: 'FACTURACION', title: 'Facturación', color: COLUMN_COLORS.FACTURACION },
  { state: 'LOGISTICA', title: 'Logística', color: COLUMN_COLORS.LOGISTICA },
  { state: 'ENTREGADO', title: 'Entregado', color: COLUMN_COLORS.ENTREGADO },
] as const
const boards: Record<string, ReturnType<typeof useOrdersBoard>> = {}
for (const c of cols) boards[c.state] = useOrdersBoard(c.state, businessDate)
</script>
