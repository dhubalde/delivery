import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import { ref } from 'vue'
import MasterCompaniesView from '@/views/master/MasterCompaniesView.vue'

const vuetify = createVuetify()

const { companies } = vi.hoisted(() => ({
  companies: [
    { id: 1, name: 'Heladería Norte', slug: 'norte', seat_limit: 10, has_branches: false, print_tickets: true, has_online_payments: true, is_active: true },
    { id: 2, name: 'Heladería Sur', slug: 'sur', seat_limit: 20, has_branches: true, print_tickets: false, has_online_payments: false, is_active: true },
    { id: 3, name: 'Kiosco Centro', slug: 'centro', seat_limit: 30, has_branches: false, print_tickets: false, has_online_payments: false, is_active: false },
  ],
}))

vi.mock('@/composables/useMaster', () => ({
  useMasterCompanies: () => ({ data: ref(companies), isLoading: ref(false) }),
}))

vi.mock('@/api/panel/master.api', () => ({
  masterApi: { onboard: vi.fn(), updateCompany: vi.fn() },
}))

const mountView = () =>
  mount(MasterCompaniesView, { global: { plugins: [vuetify] } })

const rows = (wrapper: ReturnType<typeof mountView>) =>
  wrapper.findAll('tbody tr').map((r) => r.text())

afterEach(() => {
  document.body.innerHTML = ''
})

describe('MasterCompaniesView', () => {
  it('lists every company with the flags that matter', async () => {
    const wrapper = mountView()
    await flushPromises()
    const text = wrapper.text()
    expect(text).toContain('Heladería Norte')
    expect(text).toContain('norte')
    expect(text).toContain('Heladería Sur')
    expect(text).toContain('Kiosco Centro')
    // Configuración visible por fila: tickets, Mercado Pago y estado.
    expect(text).toContain('Configurado')
    expect(text).toContain('Activa')
    expect(text).toContain('Inactiva')
  })

  it('filters rows by text search', async () => {
    const wrapper = mountView()
    await flushPromises()
    await wrapper.find('[data-test="company-search"] input').setValue('sur')
    await flushPromises()
    expect(rows(wrapper).join(' | ')).toContain('Heladería Sur')
    expect(rows(wrapper).join(' | ')).not.toContain('Heladería Norte')
  })

  it('filters rows by status', async () => {
    const wrapper = mountView()
    await flushPromises()
    const inactive = wrapper.findAll('button').find((b) => b.text() === 'Inactivas')
    expect(inactive).toBeTruthy()
    await inactive!.trigger('click')
    await flushPromises()
    expect(rows(wrapper).join(' | ')).toContain('Kiosco Centro')
    expect(rows(wrapper).join(' | ')).not.toContain('Heladería Sur')
  })

  it('sorts rows when a column header is clicked', async () => {
    const wrapper = mountView()
    await flushPromises()
    const cupo = wrapper.findAll('th').find((h) => h.text().includes('Cupo'))
    expect(cupo).toBeTruthy()
    await cupo!.trigger('click') // ascending
    await cupo!.trigger('click') // descending
    await flushPromises()
    expect(rows(wrapper)[0]).toContain('Kiosco Centro')
  })

  it('opens the edit dialog for a company', async () => {
    const wrapper = mountView()
    await flushPromises()
    await wrapper.find('[data-test="edit-company"]').trigger('click')
    await flushPromises()
    expect(document.body.textContent).toContain('Editar empresa')
    expect(document.body.textContent).toContain('Mercado Pago (pagos en línea)')
  })
})
