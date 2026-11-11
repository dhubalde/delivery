import { describe, it, expect, vi } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'

const useMyOrdersMock = vi.fn()

vi.mock('@/composables/useMyOrders', () => ({
  useMyOrders: (...args: unknown[]) => useMyOrdersMock(...args),
  useCancelMyOrder: () => ({ mutateAsync: vi.fn() }),
  getMyOrderSnapshots: vi.fn(() => []),
  updateMyOrderSnapshotState: vi.fn(),
}))

import MyOrders from '@/components/MyOrders.vue'

const vuetify = createVuetify()

const oldDate = '2026-09-26T21:36:47.107000Z'
const todayDate = () => new Date().toISOString()

const mountCard = () =>
  mount(MyOrders, {
    global: { plugins: [vuetify, createPinia()] },
  })

describe('MyOrders day filter', () => {
  it('hides orders from previous days (stale browser tracking)', async () => {
    useMyOrdersMock.mockReturnValue({
      data: ref([{ id: 7, code: 7, state: 'ENTREGADO', total: '500.00', created_at: oldDate, updated_at: oldDate }]),
      isLoading: ref(false),
      ids: ref([7]),
    })
    const wrapper = mountCard()
    await flushPromises()
    expect(wrapper.text()).not.toContain('#7')
    expect(wrapper.text()).not.toContain('¡Pedido entregado!')
  })

  it('still shows a delivered order from today', async () => {
    useMyOrdersMock.mockReturnValue({
      data: ref([{ id: 12, code: 12, state: 'ENTREGADO', total: '500.00', created_at: todayDate(), updated_at: todayDate() }]),
      isLoading: ref(false),
      ids: ref([12]),
    })
    const wrapper = mountCard()
    await flushPromises()
    expect(wrapper.text()).toContain('#12')
    expect(wrapper.text()).toContain('¡Pedido entregado!')
  })

  it('falls back to the empty state instead of stale orders', async () => {
    useMyOrdersMock.mockReturnValue({
      data: ref([{ id: 7, code: 7, state: 'ENTREGADO', total: '500.00', created_at: oldDate }]),
      isLoading: ref(false),
      ids: ref([7]),
    })
    const wrapper = mountCard()
    await flushPromises()
    expect(wrapper.text()).not.toContain('#7')
    expect(wrapper.text()).toContain('Sin pedidos pendientes')
  })
})
