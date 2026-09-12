import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { customerKey, useCustomerStore, getCustomerAccessForSlug } from '../customer.store'

describe('customer.store partition by slug', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('customerKey is slug partitioned', () => {
    expect(customerKey('acme')).toBe('customer:acme')
    expect(customerKey('beta')).toBe('customer:beta')
    expect(customerKey('acme')).not.toBe(customerKey('beta'))
  })

  it('hydrate isolates acme vs beta — no leakage', () => {
    localStorage.setItem(customerKey('acme'), JSON.stringify({ access: 'acme-token', refresh: 'r1', profile: { id: 1 } }))
    localStorage.setItem(customerKey('beta'), JSON.stringify({ access: 'beta-token', refresh: 'r2', profile: { id: 2 } }))

    const acmeStore = useCustomerStore()
    acmeStore.hydrate('acme')
    expect(acmeStore.access).toBe('acme-token')
    expect(acmeStore.profile?.id).toBe(1)

    setActivePinia(createPinia())
    const betaStore = useCustomerStore()
    betaStore.hydrate('beta')
    expect(betaStore.access).toBe('beta-token')
    expect(betaStore.profile?.id).toBe(2)
    // ensure acme token not visible
    expect(betaStore.access).not.toBe('acme-token')
  })

  it('getCustomerAccessForSlug reads only that slug', () => {
    localStorage.setItem(customerKey('acme'), JSON.stringify({ access: 'tok-acme', refresh: '', profile: null }))
    expect(getCustomerAccessForSlug('acme')).toBe('tok-acme')
    expect(getCustomerAccessForSlug('beta')).toBeNull()
  })

  it('logout removes only targeted slug', () => {
    localStorage.setItem(customerKey('acme'), JSON.stringify({ access: 'a', refresh: 'a', profile: null }))
    localStorage.setItem(customerKey('beta'), JSON.stringify({ access: 'b', refresh: 'b', profile: null }))
    const store = useCustomerStore()
    store.hydrate('acme')
    store.logout('beta')
    expect(localStorage.getItem(customerKey('beta'))).toBeNull()
    expect(localStorage.getItem(customerKey('acme'))).not.toBeNull()
    // logout current slug clears memory
    store.logout('acme')
    expect(localStorage.getItem(customerKey('acme'))).toBeNull()
    expect(store.access).toBe('')
  })

  it('persist writes to correct slug key', () => {
    const store = useCustomerStore()
    store.hydrate('acme')
    store.access = 'new-token'
    store.refresh = 'new-refresh'
    store.profile = { id: 99, phone: '555', name: 'Test', merchant_slug: 'acme', merchant_id: 1 } as any
    store.persist()
    const raw = JSON.parse(localStorage.getItem(customerKey('acme'))!)
    expect(raw.access).toBe('new-token')
    expect(localStorage.getItem(customerKey('beta'))).toBeNull()
  })
})
