import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createVuetify } from 'vuetify'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'

vi.mock('@/composables/useMenu', () => ({
  useMenu: () => ({ data: { value: null } }),
}))

vi.mock('@/composables/useMyOrders', () => ({
  useMyOrders: () => ({ data: { value: [] }, isLoading: { value: false }, ids: { value: [] } }),
  useCancelMyOrder: () => ({ mutateAsync: vi.fn() }),
  getMyOrderSnapshots: () => [],
  updateMyOrderSnapshotState: vi.fn(),
}))

import CartDrawer from '@/components/CartDrawer.vue'
import MyOrders from '@/components/MyOrders.vue'
import { useOperatorStore } from '@/stores/operator.store'

const vuetify = createVuetify()

const mountDrawer = (pinia: ReturnType<typeof createPinia>) =>
  mount(CartDrawer, {
    props: { slug: 'ice-zone' },
    global: { plugins: [vuetify, [VueQueryPlugin, { queryClient: new QueryClient() }], pinia] },
  })

describe('CartDrawer operator (manual) mode', () => {
  it('hides the customer Mi Pedido card while operator mode is active', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mountDrawer(pinia)
    expect(wrapper.findComponent(MyOrders).exists()).toBe(true)
    useOperatorStore().enter()
    await wrapper.vm.$nextTick()
    expect(wrapper.findComponent(MyOrders).exists()).toBe(false)
  })

  it('shows the customer Mi Pedido card again after the operator exits', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mountDrawer(pinia)
    const op = useOperatorStore()
    op.enter()
    await wrapper.vm.$nextTick()
    op.exit()
    await wrapper.vm.$nextTick()
    expect(wrapper.findComponent(MyOrders).exists()).toBe(true)
  })
})
