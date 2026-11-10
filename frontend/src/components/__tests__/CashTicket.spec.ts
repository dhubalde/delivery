import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CashTicket from '@/components/CashTicket.vue'

// Vuetify's auto-imported components (v-divider) break vitest's node pipeline
// on CSS imports; stubbing them is enough for this pure display component.
const mountTicket = (ticket: Record<string, unknown>) =>
  mount(CashTicket, {
    props: { ticket },
    global: { stubs: { 'v-divider': true } },
  })

describe('CashTicket', () => {
  it('renders TRANSFERENCIAS row and includes it in the fallback total', () => {
    const wrapper = mountTicket({
      business_date: '2026-11-10',
      merchant_slug: 'ice-zone',
      cashier_name: 'Caja',
      cashier_id: 1,
      totals: {
        EFECTIVO: '100.00',
        BILLETERAS_VIRTUALES: '0.00',
        TARJETAS: '0.00',
        TRANSFERENCIAS: '80.00',
        TOTAL: null,
        TOTAL_ENTREGADOS: 1,
        TOTAL_RECHAZADOS: 0,
      },
    })
    const text = wrapper.text()
    expect(text).toContain('TRANSFERENCIAS')
    expect(text).toContain('$80,00')
    // fallback total = efectivo + billeteras + tarjetas + transferencias
    expect(text).toContain('$180,00')
  })

  it('shows ticket totals when the closure already carries a TOTAL', () => {
    const wrapper = mountTicket({
      business_date: '2026-11-09',
      merchant_slug: 'ice-zone',
      totals: {
        EFECTIVO: '10.00',
        BILLETERAS_VIRTUALES: '0.00',
        TARJETAS: '0.00',
        TRANSFERENCIAS: '0.00',
        TOTAL: '10.00',
        TOTAL_ENTREGADOS: 1,
        TOTAL_RECHAZADOS: 0,
      },
    })
    expect(wrapper.text()).toContain('$10,00')
  })
})
