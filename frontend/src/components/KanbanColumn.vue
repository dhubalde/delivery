<template>
  <v-card :style="{ borderTop: `4px solid ${color}`, width: '100%', margin: '0', boxSizing: 'border-box' } as any" class="d-flex flex-column ma-0" style="min-height:420px;width:100%;margin:0;box-sizing:border-box;display:flex;flex:1 1 auto;min-width:0;max-width:none">
    <v-card-title class="d-flex justify-space-between text-subtitle-2 ma-0" style="margin:0;box-sizing:border-box;width:100%">
      <span>{{ title }}</span>
      <v-chip size="x-small">{{ orders.length }}</v-chip>
    </v-card-title>
    <v-divider class="ma-0" style="margin:0;box-sizing:border-box" />
    <v-card-text class="flex-grow-1 ma-0 pa-2" :style="(compact ? 'max-height:60vh;overflow-y:auto;margin:0;padding:8px;box-sizing:border-box;width:100%' : 'margin:0;padding:8px;box-sizing:border-box;width:100%') as any">
      <div v-if="isLoading" class="d-flex flex-column ga-2 w-100 ma-0 pa-0" style="display:flex;flex-direction:column;gap:8px;width:100%;margin:0;padding:0;box-sizing:border-box">
        <v-skeleton-loader v-for="i in 3" :key="i" type="card" :height="compact ? 60 : 80" class="ma-0 w-100" style="margin:0;width:100%;box-sizing:border-box" />
      </div>
      <div v-else-if="isError" class="text-caption text-error ma-0 pa-0 w-100" style="margin:0;padding:0;box-sizing:border-box;width:100%">Error al cargar <v-btn size="x-small" @click="$emit('retry')">Reintentar</v-btn></div>
      <div v-else-if="!orders.length" class="text-caption text-medium-emphasis text-center py-6 ma-0 w-100" style="margin:0;box-sizing:border-box;width:100%">Sin pedidos</div>
      <div v-else class="d-flex flex-column ga-2 w-100 ma-0 pa-0" style="display:flex;flex-direction:column;gap:8px;width:100%;margin:0;padding:0;box-sizing:border-box">
        <KanbanCard v-for="o in orders" :key="o.id" :order="o" :compact="compact" />
      </div>
    </v-card-text>
  </v-card>
</template>
<script setup lang="ts">
import KanbanCard from '@/components/KanbanCard.vue'
defineProps<{ title: string; color: string; orders: { id: number; code: string; state: string; fulfillment: string; cash_declared: boolean; total: string; payments: { method: string; status: string }[]; created_at?: string }[]; isLoading: boolean; isError: boolean; compact?: boolean }>()
defineEmits<{ retry: [] }>()
</script>
