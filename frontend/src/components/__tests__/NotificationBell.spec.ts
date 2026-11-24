import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import { createVuetify } from 'vuetify'
import NotificationBell from '@/components/NotificationBell.vue'
import { api } from '@/api/client'

const vuetify = createVuetify()

const notification = {
  id: 1,
  merchant: 1,
  recipient_type: 'EMPLOYEE',
  recipient_name: '',
  order: 10,
  order_code: 42,
  message: 'Pago en efectivo pendiente para pedido #42',
  type: 'PAYMENT_PENDING',
  type_label: 'Pago pendiente',
  recipient_type_label: 'Empleado',
  is_read: false,
  created_at: new Date().toISOString(),
}

vi.mock('@/api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(async () => ({ data: {} })),
    delete: vi.fn(async () => ({ data: {} })),
  },
}))

const mockList = (rows: unknown[]) => vi.mocked(api.get).mockResolvedValue({ data: rows } as never)

const mountBell = () =>
  mount(NotificationBell, {
    props: { recipientType: 'EMPLOYEE' },
    global: {
      plugins: [vuetify, [VueQueryPlugin, { queryClient: new QueryClient() }]],
    },
  })

afterEach(() => {
  document.body.innerHTML = ''
  vi.clearAllMocks()
})

describe('NotificationBell', () => {
  it('opens the dropdown when the bell button is clicked', async () => {
    mockList([notification])
    const wrapper = mountBell()
    await flushPromises()

    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(document.body.textContent).toContain('Notificaciones')
    expect(document.body.textContent).toContain('Pago en efectivo pendiente para pedido #42')
  })

  it('opens the dropdown when the click lands on the badge bubble area', async () => {
    mockList([notification])
    const wrapper = mountBell()
    await flushPromises()

    // The count bubble is not a button: the activator wrapper must own the click.
    await wrapper.find('.bell-activator').trigger('click')
    await flushPromises()

    expect(document.body.textContent).toContain('Notificaciones')
  })

  it('marks a notification as read when it is clicked', async () => {
    mockList([notification])
    const wrapper = mountBell()
    await flushPromises()
    await wrapper.find('button').trigger('click')
    await flushPromises()

    const item = Array.from(document.querySelectorAll('.notify-item'))[0] as HTMLElement
    expect(item).toBeTruthy()
    item.click()
    await flushPromises()

    expect(vi.mocked(api.post)).toHaveBeenCalledWith('/v1/notifications/1/mark-read/')
  })

  it('shows the empty state inside the dropdown', async () => {
    mockList([])
    const wrapper = mountBell()
    await flushPromises()

    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(document.body.textContent).toContain('Sin notificaciones')
  })
})
