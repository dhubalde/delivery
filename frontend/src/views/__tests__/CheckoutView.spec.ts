import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import { createVuetify } from 'vuetify'
import CheckoutView from '@/views/CheckoutView.vue'
import { redirectTo } from '@/utils/redirect'

const vuetify = createVuetify()

vi.mock('@/api/client', () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(async (url: string) => {
      if (url.includes('/v1/merchant/public/')) return { data: { has_online_payments: true } }
      return { data: {} }
    }),
  },
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useRoute: () => ({ params: { slug: 'demo' }, query: {} }),
}))

vi.mock('@/composables/useMenu', () => ({
  useMenu: () => ({ data: { value: { closed: false, is_open: true } } }),
}))

vi.mock('@/components/ClosedBanner.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/AddressMapPicker.vue', () => ({ default: { template: '<div />' } }))

vi.mock('@/utils/redirect', () => ({ redirectTo: vi.fn() }))

import { api } from '@/api/client'

async function mountCheckout() {
  const pinia = createPinia()
  // CheckoutView hydrates the cart from `cart:<slug>` on mount and snapshots
  // cart.total into the initial payments ref: seed storage before mounting.
  localStorage.setItem(
    'cart:demo',
    JSON.stringify([
      { uid: 't1', product: { id: 5, name: 'Bombo', price: 8500, product_type: 'UNIT', pote_size: null }, qty: 1, flavorIds: [], flavorNames: [] },
    ]),
  )
  const wrapper = mount(CheckoutView, {
    global: { plugins: [pinia, vuetify, [VueQueryPlugin, { queryClient: new QueryClient() }]] },
  })
  await flushPromises()
  return wrapper
}

async function fillBasics(wrapper: ReturnType<typeof mount>) {
  const inputs = wrapper.findAll('input')
  await inputs[0].setValue('Ana Pérez')
  await inputs[1].setValue('3424508000')
  await inputs[2].setValue('San Martín 1234')
}

async function clickSubmit(wrapper: ReturnType<typeof mount>) {
  const btn = wrapper.findAll('button').find((b) => b.text().includes('Confirmar pedido'))
  await btn?.trigger('click')
  await flushPromises()
}

beforeEach(() => {
  vi.clearAllMocks()
  // Cart persists in localStorage keyed by slug: never leak between tests.
  localStorage.clear()
})

describe('CheckoutView payments', () => {
  it('web + online mode: creates the order then redirects to the MP checkout', async () => {
    vi.mocked(api.post).mockImplementation(async (url: string) => {
      if (url.endsWith('/orders') || url.endsWith('/orders/')) return { data: { id: 1, code: 1, total: '8500.00' } }
      return { data: { init_point: 'https://mp/checkout/init' } }
    })
    const wrapper = await mountCheckout()
    await fillBasics(wrapper)
    // Switch to "Pagar en línea"
    const onlineBtn = wrapper.findAll('button').find((b) => b.text().includes('Pagar en línea'))
    expect(onlineBtn).toBeTruthy() // option offered because has_online_payments
    await onlineBtn?.trigger('click')
    await clickSubmit(wrapper)
    const calls = vi.mocked(api.post).mock.calls
    const create = calls.find(([u]) => String(u).includes('/orders'))
    expect((create?.[1] as { payments: { method: string; amount: string }[] }).payments).toEqual([
      { method: 'ONLINE', amount: '8500' },
    ])
    expect(calls.some(([u]) => String(u).includes('/orders/1/pay'))).toBe(true)
    expect(redirectTo).toHaveBeenCalledWith('https://mp/checkout/init')
  })

  it('web + cash mode: no online pay call, cash payment declared', async () => {
    vi.mocked(api.post).mockImplementation(async (url: string) => {
      if (url.endsWith('/orders') || url.endsWith('/orders/')) return { data: { id: 2, code: 2, total: '8500.00' } }
      return { data: { init_point: 'https://mp/x' } }
    })
    const wrapper = await mountCheckout()
    await fillBasics(wrapper)
    await clickSubmit(wrapper)
    const calls = vi.mocked(api.post).mock.calls
    const create = calls.find(([u]) => String(u).includes('/orders'))
    expect((create?.[1] as { payments: { method: string; amount: string }[] }).payments).toEqual([
      { method: 'EFECTIVO', amount: '8500' },
    ])
    expect(calls.some(([u]) => String(u).includes('/pay'))).toBe(false)
    expect(redirectTo).not.toHaveBeenCalled()
  })
})
