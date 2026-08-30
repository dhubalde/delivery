<template>
  <v-card :style="{ borderTop: `4px solid ${color}` }" class="d-flex flex-column" style="min-height: 420px">
    <v-card-title class="d-flex justify-space-between text-subtitle-2">
      <span>{{ title }}</span>
      <v-chip size="x-small">{{ orders.length }}</v-chip>
    </v-card-title>
    <v-divider />
    <v-card-text class="flex-grow-1" :style="compact ? 'max-height: 60vh; overflow-y: auto' : undefined">
      <div v-if="isLoading" class="d-flex flex-column ga-2">
        <v-skeleton-loader v-for="i in 3" :key="i" type="card" :height="compact ? 60 : 80" />
      </div>
      <div v-else-if="isError" class="text-caption text-error">Error al cargar <v-btn size="x-small" @click="$emit('retry')">Reintentar</v-btn></div>
      <div v-else-if="!orders.length" class="text-caption text-medium-emphasis text-center py-6">Sin pedidos</div>
      <KanbanCard v-for="o in orders" :key="o.id" :order="o" :compact="compact" />
    </v-card-text>
  </v-card>
</template>
<script setup lang="ts">
import KanbanCard from '@/components/KanbanCard.vue'
defineProps<{ title: string; color: string; orders: { id: number; code: string; state: string; fulfillment: string; cash_declared: boolean; total: string; payments: { method: string; status: string }[]; created_at?: string }[]; isLoading: boolean; isError: boolean; compact?: boolean }>()
defineEmits<{ retry: [] }>()
</script>
