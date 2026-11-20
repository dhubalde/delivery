<template>
  <v-container fluid class="pa-4">
    <v-row align="center" class="mb-3">
      <v-col cols="12" md="6">
        <h2 class="text-h6 mb-1">Empresas cliente</h2>
        <div class="text-caption text-medium-emphasis">
          Buscá, filtrá y ordená por columna. El lápiz abre la configuración de cada empresa.
        </div>
      </v-col>
      <v-col cols="12" md="6" class="text-md-right">
        <v-btn color="primary" prepend-icon="mdi-plus" @click="dlg = true">Onboarding</v-btn>
      </v-col>
    </v-row>

    <DataTableCard
      v-model:search="search"
      :headers="headers"
      :items="filtered"
      :total="list.length"
      :search-keys="['name', 'slug']"
      search-label="Buscar por nombre o slug"
      search-test-id="company-search"
      :loading="isLoading"
      no-data-text="Sin empresas que coincidan con la búsqueda."
    >
      <template #filters>
        <v-btn-toggle v-model="status" mandatory density="compact" variant="outlined" divided>
          <v-btn value="all" size="small">Todas</v-btn>
          <v-btn value="active" size="small">Activas</v-btn>
          <v-btn value="inactive" size="small">Inactivas</v-btn>
        </v-btn-toggle>
      </template>
        <template #item.name="{ item }">
          <div class="font-weight-medium">{{ item.name }}</div>
          <div class="text-caption text-medium-emphasis">{{ item.slug }}</div>
        </template>
        <template #item.has_branches="{ item }">
          <v-icon v-if="item.has_branches" color="success" size="small">mdi-check-circle</v-icon>
          <span v-else class="text-medium-emphasis">—</span>
        </template>
        <template #item.print_tickets="{ item }">
          <v-chip v-if="item.print_tickets" size="small" variant="tonal" color="primary">Sí</v-chip>
          <span v-else class="text-medium-emphasis">—</span>
        </template>
        <template #item.has_online_payments="{ item }">
          <v-chip v-if="item.has_online_payments" size="small" variant="tonal" color="success">
            Configurado
          </v-chip>
          <span v-else class="text-medium-emphasis">—</span>
        </template>
        <template #item.is_active="{ item }">
          <v-chip :color="item.is_active ? 'success' : 'default'" variant="tonal" size="small">
            {{ item.is_active ? 'Activa' : 'Inactiva' }}
          </v-chip>
        </template>
      <template #item.actions="{ item }">
        <v-btn
          icon="mdi-pencil"
          variant="text"
          size="small"
          color="primary"
          data-test="edit-company"
          :title="`Editar ${item.name}`"
          @click="openEdit(item)"
        />
      </template>
    </DataTableCard>

    <v-dialog v-model="dlg" max-width="520">
      <v-card>
        <v-card-title>Nueva empresa</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.name" label="Nombre fantasía *" density="compact" />
          <v-text-field v-model="form.slug" label="Slug *" density="compact" hint="minúsculas-sin-espacios" />
          <v-text-field v-model="form.logo_url" label="Logo URL" density="compact" />
          <v-select v-model="form.seat_limit" :items="[10,20,30]" label="Cupo de usuarios *" density="compact" />
          <v-switch v-model="form.has_branches" label="Tiene sucursales" color="primary" />
          <v-text-field v-model="form.admin_username" label="Admin inicial *" density="compact" />
          <v-text-field v-model="form.admin_password" label="Clave inicial *" :type="showPass ? 'text' : 'password'"
            :append-inner-icon="showPass ? 'mdi-eye-off' : 'mdi-eye'" density="compact"
            hint="8-12, número, mayúscula y especial"
            @click:append-inner="showPass = !showPass" />
          <v-alert v-if="err" type="error" density="compact">{{ err }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dlg=false">Cancelar</v-btn>
          <v-btn color="primary" :loading="saving" @click="save">Crear</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="edlg" max-width="520">
      <v-card>
        <v-card-title>Editar empresa</v-card-title>
        <v-card-text>
          <v-text-field v-model="eform.name" label="Nombre fantasía *" density="compact" />
          <v-text-field v-model="eform.logo_url" label="Logo URL" density="compact" />
          <v-select v-model="eform.seat_limit" :items="[10,20,30]" label="Cupo de usuarios *" density="compact" />
          <v-switch v-model="eform.has_branches" label="Tiene sucursales" color="primary" />
          <v-switch v-model="eform.print_tickets" label="Imprime tickets en comandera" color="primary" hint="Al pasar un pedido a Preparación se encola el ticket" persistent-hint />
          <v-switch v-model="eform.is_active" label="Activa" color="primary" />
          <v-divider class="my-2" />
          <div class="text-subtitle-2 mb-1">Mercado Pago (pagos en línea)</div>
          <v-text-field
            v-model="eform.mp_access_token"
            label="Access token"
            density="compact"
            type="password"
            autocomplete="off"
            hint="Dejar vacío para no cambiar"
            persistent-hint
          />
          <v-text-field
            v-model="eform.mp_webhook_secret"
            label="Webhook secret"
            density="compact"
            type="password"
            autocomplete="off"
            hint="Dejar vacío para no cambiar"
            persistent-hint
          />
          <v-alert v-if="err" type="error" density="compact">{{ err }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="edlg=false">Cancelar</v-btn>
          <v-btn color="primary" :loading="saving" @click="saveEdit">Guardar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useMasterCompanies } from '@/composables/useMaster'
import { masterApi } from '@/api/panel/master.api'
import type { Company } from '@/api/panel/master.api'
import DataTableCard from '@/components/DataTableCard.vue'

const { data, isLoading } = useMasterCompanies()
const list = computed(() => (data.value ?? []) as Company[])

const search = ref('')
const status = ref<'all' | 'active' | 'inactive'>('all')
const filtered = computed(() =>
  list.value.filter((c) => {
    if (status.value === 'active') return c.is_active
    if (status.value === 'inactive') return !c.is_active
    return true
  }),
)

// Every column is sortable by clicking its header; actions is not.
const headers = [
  { title: 'Empresa', key: 'name' },
  { title: 'Cupo', key: 'seat_limit', align: 'end' as const },
  { title: 'Sucursales', key: 'has_branches', align: 'center' as const },
  { title: 'Tickets', key: 'print_tickets', align: 'center' as const },
  { title: 'Mercado Pago', key: 'has_online_payments', align: 'center' as const },
  { title: 'Estado', key: 'is_active', align: 'center' as const },
  { title: '', key: 'actions', sortable: false, align: 'end' as const },
]

const dlg = ref(false)
const saving = ref(false)
const err = ref('')
const showPass = ref(false)
const form = reactive({ name: '', slug: '', logo_url: '', seat_limit: 10, has_branches: false, admin_username: '', admin_password: '' })

async function save() {
  saving.value = true; err.value = ''
  try {
    await masterApi.onboard({ ...form, logo_url: form.logo_url || undefined })
    dlg.value = false
    Object.assign(form, { name: '', slug: '', logo_url: '', seat_limit: 10, has_branches: false, admin_username: '', admin_password: '' })
  } catch (e: unknown) {
    err.value = (e as { response?: { data?: { error?: { message?: string }, slug?: string } } })?.response?.data?.error?.message
      ?? (e as { response?: { data?: { slug?: string } } })?.response?.data?.slug ?? 'Error'
  } finally { saving.value = false }
}

const edlg = ref(false)
const editing = ref<number | null>(null)
const eform = reactive({
  name: '', logo_url: '', seat_limit: 10, has_branches: false,
  print_tickets: false, is_active: true,
  mp_access_token: '', mp_webhook_secret: '',
})

function openEdit(c: Company) {
  editing.value = c.id
  // Credentials are never returned by the API; leave blank to keep current values.
  Object.assign(eform, {
    name: c.name, logo_url: '', seat_limit: c.seat_limit, has_branches: c.has_branches,
    print_tickets: !!c.print_tickets, is_active: c.is_active,
    mp_access_token: '', mp_webhook_secret: '',
  })
  err.value = ''; edlg.value = true
}

async function saveEdit() {
  if (!editing.value) return
  saving.value = true; err.value = ''
  try {
    const payload: Record<string, unknown> = {
      name: eform.name, logo_url: eform.logo_url, seat_limit: eform.seat_limit,
      has_branches: eform.has_branches, print_tickets: eform.print_tickets, is_active: eform.is_active,
    }
    // Only send credentials when the user typed a value; blank means "keep as is".
    if (eform.mp_access_token.trim()) payload.mp_access_token = eform.mp_access_token.trim()
    if (eform.mp_webhook_secret.trim()) payload.mp_webhook_secret = eform.mp_webhook_secret.trim()
    await masterApi.updateCompany(editing.value, payload)
    edlg.value = false; editing.value = null
  } catch (e: unknown) {
    err.value = (e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message ?? 'Error'
  } finally { saving.value = false }
}
</script>
