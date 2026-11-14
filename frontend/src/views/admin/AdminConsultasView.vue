<template>
  <v-container>
    <div class="mb-3">
      <h2 class="text-h6" style="font-family: Comfortaa">Consultas — tickets de pedidos</h2>
      <div class="text-caption text-medium-emphasis">
        Historial para reclamos: buscá por fecha, código o cliente y reimprimí el ticket.
      </div>
    </div>
    <v-card variant="tonal" class="mb-3">
      <v-card-text class="d-flex flex-wrap ga-2 align-center py-2">
        <v-text-field v-model="startDate" type="date" density="compact" hide-details label="Desde" style="max-width: 180px" />
        <v-text-field v-model="endDate" type="date" density="compact" hide-details label="Hasta" style="max-width: 180px" />
        <v-text-field
          v-model="search"
          density="compact"
          hide-details
          clearable
          label="Código o cliente (nombre/teléfono)"
          style="max-width: 280px"
          @keyup.enter="doSearch"
        />
        <v-btn color="primary" density="compact" @click="doSearch">Buscar</v-btn>
      </v-card-text>
    </v-card>
    <v-skeleton-loader v-if="isLoading" type="table" />
    <v-alert v-else-if="error" type="warning" density="compact">No se pudo cargar el historial.</v-alert>
    <template v-else>
      <v-alert v-if="!rows.length" type="info" variant="tonal" density="compact">
        Sin pedidos para esos filtros.
      </v-alert>
      <v-table v-else density="compact">
        <thead>
          <tr>
            <th>Pedido</th>
            <th>Fecha y hora</th>
            <th>Cliente</th>
            <th>Estado</th>
            <th class="text-right">Total</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="o in rows" :key="o.id">
            <td>#{{ o.code }}</td>
            <td>{{ when(o) }}</td>
            <td>{{ o.customer_name }}<span v-if="o.customer_phone" class="text-caption text-medium-emphasis"> · {{ o.customer_phone }}</span></td>
            <td><v-chip size="x-small" variant="tonal" :color="chipColor(o.state)">{{ o.state }}</v-chip></td>
            <td class="text-right">${{ o.total }}</td>
            <td class="text-right">
              <v-btn size="small" variant="text" prepend-icon="mdi-receipt-text" @click="openTicket(o)">Ver ticket</v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>
    </template>
    <v-dialog v-model="ticketDlg" max-width="360">
      <v-card>
        <v-card-title class="text-subtitle-2">Ticket #{{ current?.code }}</v-card-title>
        <v-card-text>
          <!-- eslint-disable-next-line vue/no-v-html — ticket HTML is built locally from server data, escaped -->
          <div v-if="current" v-html="ticketHtml" style="font-family: 'Courier New', monospace; font-size: 12px" />
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="ticketDlg = false">Cerrar</v-btn>
          <v-spacer />
          <v-btn color="primary" prepend-icon="mdi-printer" @click="reprint">Reimprimir</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
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

type Row = TicketOrder

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
