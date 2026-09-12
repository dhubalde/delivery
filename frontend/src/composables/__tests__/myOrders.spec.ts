import { describe, it, expect, beforeEach } from 'vitest'
import { myOrdersKey, getMyOrderIdsForSlug, addMyOrderIdForSlug, removeMyOrderIdForSlug } from '../useMyOrders'

describe('myOrders partition by slug', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('myOrdersKey is slug partitioned', () => {
    expect(myOrdersKey('acme')).toBe('myOrders:acme')
    expect(myOrdersKey('beta')).toBe('myOrders:beta')
    expect(myOrdersKey('acme')).not.toBe(myOrdersKey('beta'))
  })

  it('getMyOrderIdsForSlug isolates acme vs beta', () => {
    localStorage.setItem(myOrdersKey('acme'), JSON.stringify([1, 2, 3]))
    localStorage.setItem(myOrdersKey('beta'), JSON.stringify([99]))
    expect(getMyOrderIdsForSlug('acme')).toEqual([1, 2, 3])
    expect(getMyOrderIdsForSlug('beta')).toEqual([99])
  })

  it('addMyOrderIdForSlug only affects that slug', () => {
    addMyOrderIdForSlug(10, 'acme')
    addMyOrderIdForSlug(20, 'beta')
    expect(getMyOrderIdsForSlug('acme')).toContain(10)
    expect(getMyOrderIdsForSlug('acme')).not.toContain(20)
    expect(getMyOrderIdsForSlug('beta')).toContain(20)
    expect(getMyOrderIdsForSlug('beta')).not.toContain(10)
  })

  it('empty beta never shows acme orders', () => {
    addMyOrderIdForSlug(1, 'acme')
    addMyOrderIdForSlug(2, 'acme')
    expect(getMyOrderIdsForSlug('beta').length).toBe(0)
    expect(getMyOrderIdsForSlug('acme').length).toBe(2)
  })

  it('removeMyOrderIdForSlug only removes from that slug', () => {
    addMyOrderIdForSlug(1, 'acme')
    addMyOrderIdForSlug(1, 'beta')
    removeMyOrderIdForSlug(1, 'acme')
    expect(getMyOrderIdsForSlug('acme')).not.toContain(1)
    expect(getMyOrderIdsForSlug('beta')).toContain(1)
  })

  it('caps at 20 most recent', () => {
    for (let i = 0; i < 25; i++) addMyOrderIdForSlug(i, 'acme')
    const ids = getMyOrderIdsForSlug('acme')
    expect(ids.length).toBe(20)
    // most recent first
    expect(ids[0]).toBe(24)
  })
})
