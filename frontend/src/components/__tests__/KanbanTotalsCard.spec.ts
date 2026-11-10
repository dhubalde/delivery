import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import { createVuetify } from 'vuetify'
import KanbanTotalsCard from '@/components/KanbanTotalsCard.vue'

const vuetify = createVuetify()

vi.mock('@/api/panel/cash.api', () => ({
  cashApi: {
    preview: vi.fn(async () => ({
      totals: {
        EFECTIVO: '100.00',
        BILLETERAS_VIRTUALES: '0.00',
        TARJETAS: '0.00',
        TRANSFERENCIAS: '80.00',
        TOTAL: '180.00',
        TOTAL_ENTREGADOS: 2,
        TOTAL_RECHAZADOS: 0,
      },
    })),
  },
}))

const mountCard = () =>
  mount(KanbanTotalsCard, {
    props: { fallbackOrders: [] },
    global: {
      plugins: [vuetify, [VueQueryPlugin, { queryClient: new QueryClient() }]],
      stubs: { 'v-divider': true, 'v-skeleton-loader': true },
    },
  })

beforeEach(() => {
  vi.clearAllMocks()
})

describe('KanbanTotalsCard', () => {
  it('shows a Transferencias row from the preview totals', async () => {
    const wrapper = mountCard()
    await flushPromises()
    const text = wrapper.text()
    expect(text).toContain('Transferencias')
    expect(text).toContain('$80,00')
    // total = efectivo + billeteras + tarjetas + transferencias
    expect(text).toContain('$180,00')
  })
})
