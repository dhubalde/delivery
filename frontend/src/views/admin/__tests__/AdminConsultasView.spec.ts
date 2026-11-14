import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import { createVuetify } from 'vuetify'
import AdminConsultasView from '@/views/admin/AdminConsultasView.vue'

const vuetify = createVuetify()

vi.mock('@/api/client', () => ({
  api: { get: vi.fn(async () => ({ data: [] })) },
}))

vi.mock('@/composables/useMerchant', async () => {
  const { ref } = await import('vue')
  return { useMerchant: () => ({ data: ref(undefined) }) }
})

import { api } from '@/api/client'

const mountView = () =>
  mount(AdminConsultasView, {
    global: {
      plugins: [vuetify, [VueQueryPlugin, { queryClient: new QueryClient() }]],
    },
  })

beforeEach(() => {
  vi.clearAllMocks()
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('AdminConsultasView', () => {
  it('opens with today by default (claims can arrive the same day)', async () => {
    mountView()
    await flushPromises()
    const today = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Argentina/Buenos_Aires' })
    const first = vi.mocked(api.get).mock.calls[0]
    expect(first?.[1]?.params as Record<string, string>).toMatchObject({
      business_date: today,
      business_date_to: today,
    })
  })

  it('searches in real time with debounce, sending q (code, name or phone)', async () => {
    const wrapper = mountView()
    await flushPromises()
    // Initial load: yesterday window, no q.
    const firstCall = vi.mocked(api.get).mock.calls[0]
    expect(firstCall?.[1]?.params).not.toHaveProperty('q')

    // Typing a phone does not require Enter: it debounces and re-queries with q.
    const inputs = wrapper.findAll('input')
    await inputs[2].setValue('3456')
    await vi.advanceTimersByTimeAsync(400)
    await flushPromises()
    const calls = vi.mocked(api.get).mock.calls
    const qCall = calls.find(([, cfg]) => (cfg?.params as Record<string, string> | undefined)?.q === '3456')
    expect(qCall).toBeTruthy()

    // Clearing the field goes back to the default list (no way to get stuck).
    await inputs[2].setValue('')
    await vi.advanceTimersByTimeAsync(400)
    await flushPromises()
    const cleared = vi.mocked(api.get).mock.calls[vi.mocked(api.get).mock.calls.length - 1]
    expect((cleared?.[1]?.params as Record<string, string> | undefined)).not.toHaveProperty('q')
  })
})
