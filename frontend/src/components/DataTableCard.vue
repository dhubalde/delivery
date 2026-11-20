<template>
  <v-card rounded="lg">
    <v-card-title class="d-flex flex-wrap align-center ga-3 py-3">
      <v-text-field
        :model-value="search"
        :data-test="searchTestId"
        :label="searchLabel"
        prepend-inner-icon="mdi-magnify"
        density="compact"
        variant="outlined"
        hide-details
        clearable
        class="table-search"
        @update:model-value="onSearch"
      />
      <slot name="filters" />
      <v-spacer />
      <v-chip v-if="showCount" size="small" variant="tonal">{{ items.length }} de {{ total ?? items.length }}</v-chip>
    </v-card-title>
    <v-divider />
    <v-data-table
      :headers="headers"
      :items="items"
      :search="clientSearch ? search : undefined"
      :filter-keys="clientSearch ? searchKeys : undefined"
      :loading="loading"
      :item-value="itemValue"
      :density="density"
      :items-per-page="itemsPerPage"
      :items-per-page-options="[10, 25, 50, -1]"
      hover
    >
      <template v-for="name in itemSlotNames" :key="name" #[name]="slotProps">
        <slot :name="name" v-bind="slotProps ?? {}" />
      </template>
      <template #no-data>
        <div class="pa-6 text-center text-medium-emphasis">
          <slot name="no-data">{{ noDataText }}</slot>
        </div>
      </template>
    </v-data-table>
  </v-card>
</template>

<script setup lang="ts">
import { computed, useSlots } from 'vue'

interface TableHeader {
  title: string
  key: string
  align?: 'start' | 'center' | 'end'
  sortable?: boolean
  width?: string
}

const props = withDefaults(
  defineProps<{
    headers: TableHeader[]
    items: unknown[]
    total?: number
    search?: string
    // Keys for client-side filtering. Leave empty when the server already filtered.
    searchKeys?: string[]
    searchLabel?: string
    searchTestId?: string
    loading?: boolean
    itemValue?: string
    density?: 'compact' | 'comfortable'
    itemsPerPage?: number
    noDataText?: string
    showCount?: boolean
  }>(),
  {
    total: undefined,
    search: '',
    searchKeys: () => [],
    searchLabel: 'Buscar',
    searchTestId: 'table-search',
    loading: false,
    itemValue: 'id',
    density: 'comfortable',
    itemsPerPage: 10,
    noDataText: 'Sin resultados.',
    showCount: true,
  },
)

const emit = defineEmits<{ 'update:search': [value: string] }>()

const slots = useSlots()
const itemSlotNames = computed(() => Object.keys(slots).filter((name) => name.startsWith('item.')))
const clientSearch = computed(() => props.searchKeys.length > 0)

function onSearch(value: unknown) {
  emit('update:search', typeof value === 'string' ? value : '')
}
</script>
