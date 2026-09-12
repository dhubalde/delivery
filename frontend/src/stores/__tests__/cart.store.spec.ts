import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { cartKey, useCartStore } from '../cart.store'

describe('cart.store partition by slug', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('cartKey is slug partitioned', () => {
    expect(cartKey('acme')).toBe('cart:acme')
    expect(cartKey('beta')).toBe('cart:beta')
    expect(cartKey('acme')).not.toBe(cartKey('beta'))
  })

  it('hydrate isolates acme vs beta', () => {
    localStorage.setItem(cartKey('acme'), JSON.stringify([{ uid: '1', product: { price: 10 }, qty: 2 }]))
    localStorage.setItem(cartKey('beta'), JSON.stringify([{ uid: '2', product: { price: 99 }, qty: 1 }]))

    const acmeStore = useCartStore()
    acmeStore.hydrate('acme')
    expect(acmeStore.items.length).toBe(1)
    expect(acmeStore.items[0].uid).toBe('1')

    // second store instance still shares pinia but we re-hydrate with beta via clearMemory pattern
    const betaStore = useCartStore()
    // force rehydrate by resetting _hydratedSlug trick: create new pinia
    setActivePinia(createPinia())
    const beta2 = useCartStore()
    beta2.hydrate('beta')
    expect(beta2.items.length).toBe(1)
    expect(beta2.items[0].uid).toBe('2')

    // ensure acme data not visible in beta store
    expect(beta2.items.some((i) => i.uid === '1')).toBe(false)
  })

  it('add persists to slug-specific key only', () => {
    const store = useCartStore()
    store.hydrate('acme')
    const product = { price: '100.00', product_type: 'UNIT', pote_size: null } as any
    // stub crypto.randomUUID if missing
    if (!globalThis.crypto?.randomUUID) {
      // @ts-ignore
      globalThis.crypto = { ...globalThis.crypto, randomUUID: () => 'uuid-' + Math.random() }
    }
    store.add(product, [], [])
    expect(JSON.parse(localStorage.getItem(cartKey('acme')) || '[]').length).toBe(1)
    expect(localStorage.getItem(cartKey('beta'))).toBeNull()
  })

  it('empty beta never shows acme items', () => {
    const acme = useCartStore()
    acme.hydrate('acme')
    const product = { price: '10.00', product_type: 'UNIT', pote_size: null } as any
    acme.add(product, [], [])

    setActivePinia(createPinia())
    const beta = useCartStore()
    beta.hydrate('beta')
    expect(beta.items.length).toBe(0)
    expect(beta.isEmpty).toBe(true)
    expect(acme.items.length).toBe(1)
  })

  it('clear(beta) removes only beta key', () => {
    localStorage.setItem(cartKey('acme'), JSON.stringify([{ uid: 'a' }]))
    localStorage.setItem(cartKey('beta'), JSON.stringify([{ uid: 'b' }]))
    const store = useCartStore()
    store.hydrate('acme')
    store.clear('beta')
    expect(localStorage.getItem(cartKey('beta'))).toBeNull()
    expect(JSON.parse(localStorage.getItem(cartKey('acme')) || '[]').length).toBe(1)
  })
})
