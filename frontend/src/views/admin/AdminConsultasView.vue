<template>
  <v-container>
    <PageHeader
      title="Consultas — tickets de pedidos"
      subtitle="Historial para reclamos: buscá por fecha, código o cliente y reimprimí el ticket."
    />
    <v-alert v-if="error" type="warning" density="compact" class="mb-2">No se pudo cargar el historial.</v-alert>
    <DataTableCard
      v-model:search="search"
      :headers="headers"
      :items="rows"
      search-label="Código o cliente (nombre/teléfono)"
      :loading="isLoading"
      no-data-text="Sin pedidos para esos filtros."
    >
      <template #filters>
        <v-text-field
          v-model="startDate"
          type="date"
          label="Desde"
          density="compact"
          variant="outlined"
          hide-details
          style="max-width: 180px"
        />
        <v-text-field
          v-model="endDate"
          type="date"
          label="Hasta"
          density="compact"
          variant="outlined"
          hide-details
          style="max-width: 180px"
        />
        <v-btn color="primary" variant="tonal" @click="doSearch">Buscar</v-btn>
      </template>
      <template #item.code="{ item }">
        <span class="font-weight-medium">#{{ item.code }}</span>
      </template>
      <template #item.created_at="{ item }">
        <span class="text-caption">{{ when(item as unknown as Row) }}</span>
      </template>
      <template #item.customer_name="{ item }">
        {{ item.customer_name }}
        <span v-if="item.customer_phone" class="text-caption text-medium-emphasis"> · {{ item.customer_phone }}</span>
      </template>
      <template #item.state="{ item }">
        <v-chip size="x-small" variant="tonal" :color="chipColor(String(item.state))">{{ item.state }}</v-chip>
      </template>
      <template #item.total="{ item }">
        <span class="font-weight-medium">${{ item.total }}</span>
      </template>
      <template #item.actions="{ item }">
        <v-btn size="small" variant="text" color="primary" prepend-icon="mdi-receipt-text" @click="openTicket(item as unknown as Row)">
          Ver ticket
        </v-btn>
      </template>
    </DataTableCard>
    <FormDialog
      v-model="ticketDlg"
      :title="`Ticket #${current?.code ?? ''}`"
      :max-width="360"
      hide-submit
      cancel-label="Cerrar"
    >
      <!-- eslint-disable-next-line vue/no-v-html — ticket HTML is built locally from server data, escaped -->
      <div v-if="current" v-html="ticketHtml" style="font-family: 'Courier New', monospace; font-size: 12px" />
      <template #actions>
        <v-btn color="primary" prepend-icon="mdi-printer" @click="reprint">Reimprimir</v-btn>
      </template>
    </FormDialog>
  </v-container>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { api } from '@/api/client'
import { useMerchant } from '@/composables/useMerchant'
import { printTicket, buildTicketHtml, ticketWhen } from '@/utils/ticket'
import type { TicketOrder } from '@/api/panel/printing.api'
import { qk } from '@/queries/keys'
import { DataTableCard, FormDialog, PageHeader } from '@/design'

type Row = TicketOrder

// Server-side filtering: the query already sends q, so the table must not filter again.
const headers = [
  { title: 'Pedido', key: 'code' },
  { title: 'Fecha y hora', key: 'created_at' },
  { title: 'Cliente', key: 'customer_name' },
  { title: 'Estado', key: 'state', align: 'center' as const },
  { title: 'Total', key: 'total', align: 'end' as const },
  { title: '', key: 'actions', sortable: false, align: 'end' as const },
]

function isoDaysAgo(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return d.toLocaleDateString('en-CA', { timeZone: 'America/Argentina/Buenos_Aires' })
}

// Default window: today — claims can also arrive the same day.
const startDate = ref(isoDaysAgo(0))
const endDate = ref(isoDaysAgo(0))
const search = ref('')
const applied = ref<{ start: string; end: string; search: string }>({
  start: isoDaysAgo(0),
  end: isoDaysAgo(0),
  search: '',
})

function applyNow() {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
  applied.value = {
    start: startDate.value || isoDaysAgo(0),
    end: endDate.value || isoDaysAgo(0),
    search: (search.value || '').trim(),
  }
}

function doSearch() {
  applyNow()
}

// Live search: re-query shortly after the last edit of any filter, so there is
// no dead end — clearing the field or changing dates goes back on its own.
// Enter and the Buscar button still apply immediately.
let debounceTimer: ReturnType<typeof setTimeout> | null = null
watch([startDate, endDate, search], () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(applyNow, 400)
})

const params = computed(() => {
  const p: Record<string, string> = { business_date: applied.value.start, business_date_to: applied.value.end }
  // Unified q: matches order code, customer name or phone on the backend.
  const s = applied.value.search
  if (s) p.q = s
  return p
})

const { data, isLoading, error } = useQuery({
  queryKey: computed(() => qk.consultasOrders(params.value as never)),
  queryFn: async () => (await api.get('/v1/orders/', { params: params.value })).data as Row[],
})

const rows = computed<Row[]>(() => (data.value as Row[] | undefined) ?? [])

function when(o: Row): string {
  return ticketWhen(o)
}

function chipColor(state: string): string {
  return ({ RECIBIDO: 'warning', PREPARACION: 'deep-orange', FACTURACION: 'primary', LOGISTICA: 'purple', ENTREGADO: 'success', CANCELADO: 'error' } as Record<string, string>)[state] ?? 'default'
}

const ticketDlg = ref(false)
const current = ref<Row | null>(null)
const ticketHtml = computed(() => (current.value ? buildTicketHtml(current.value, companyName.value) : ''))

const { data: merchantData } = useMerchant()
const companyName = computed(() => (merchantData.value as { name?: string } | undefined)?.name ?? '')

function openTicket(o: Row) {
  current.value = o
  ticketDlg.value = true
}

function reprint() {
  if (current.value) printTicket(current.value, companyName.value)
}
</script>
