import { describe, it, expect } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import { ref } from 'vue'
import DataTableCard from '@/design/DataTableCard.vue'

const vuetify = createVuetify()

interface Row { id: number; name: string; city: string }

const items: Row[] = [
  { id: 1, name: 'Heladería Norte', city: 'Rosario' },
  { id: 2, name: 'Heladería Sur', city: 'Funes' },
  { id: 3, name: 'Kiosco Centro', city: 'Roldán' },
]

const headers = [
  { title: 'Nombre', key: 'name' },
  { title: 'Ciudad', key: 'city' },
]

const mountTable = (props: Record<string, unknown> = {}) =>
  mount(DataTableCard, {
    props: { headers, items, search: '', searchKeys: ['name'], ...props },
    global: { plugins: [vuetify] },
  })

const rows = (wrapper: ReturnType<typeof mountTable>) =>
  wrapper.findAll('tbody tr').map((r) => r.text())

describe('DataTableCard', () => {
  it('renders every row and a count of visible rows', async () => {
    const wrapper = mountTable()
    await flushPromises()
    expect(rows(wrapper)).toHaveLength(3)
    expect(wrapper.text()).toContain('3 de 3')
  })

  it('filters rows with the search box and emits the update', async () => {
    const wrapper = mountTable()
    await flushPromises()
    await wrapper.find('[data-test="table-search"] input').setValue('sur')
    await flushPromises()
    const emits = wrapper.emitted('update:search') ?? []
    expect(emits[emits.length - 1]).toEqual(['sur'])
  })

  it('filters rows client-side when searchKeys are given', async () => {
    const search = ref('')
    const wrapper = mount(DataTableCard, {
      props: { headers, items, search: search.value, searchKeys: ['name'] },
      global: { plugins: [vuetify] },
    })
    await flushPromises()
    await wrapper.setProps({ search: 'Kiosco' })
    await flushPromises()
    expect(rows(wrapper).join(' | ')).toContain('Kiosco Centro')
    expect(rows(wrapper).join(' | ')).not.toContain('Heladería Norte')
  })

  it('shows the empty message when nothing matches', async () => {
    const wrapper = mountTable({ search: 'no-existe' })
    await flushPromises()
    expect(wrapper.text()).toContain('Sin resultados')
  })

  it('forwards item slots and extra filters', async () => {
    const wrapper = mount(DataTableCard, {
      props: { headers, items, search: '', searchKeys: ['name'] },
      slots: {
        'item.name': '<span class="custom-name">{{ params.item.name }}</span>',
        filters: '<button class="my-filter">Activas</button>',
      },
      global: { plugins: [vuetify] },
    })
    await flushPromises()
    expect(wrapper.findAll('.custom-name')).toHaveLength(3)
    expect(wrapper.find('.my-filter').exists()).toBe(true)
  })
})
