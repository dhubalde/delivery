import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { operatorActiveKey, useOperatorStore, coordinatorMethods, isManualBodySource } from '../operator.store'

describe('operator.store manual-entry mode', () => {
  beforeEach(() => {
    sessionStorage.clear()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('operatorActiveKey persists the flag in sessionStorage', () => {
    expect(operatorActiveKey).toBe('operator:manual')
  })

  it('enter() sets active and survives a fresh store instance', () => {
    const store = useOperatorStore()
    store.enter()
    expect(store.active).toBe(true)
    setActivePinia(createPinia())
    const fresh = useOperatorStore()
    fresh.hydrate()
    expect(fresh.active).toBe(true)
  })

  it('exit() clears the flag in storage and memory', () => {
    const store = useOperatorStore()
    store.enter()
    store.exit()
    expect(store.active).toBe(false)
    expect(sessionStorage.getItem(operatorActiveKey)).toBeNull()
  })

  it('phone-request methods are cash + transfer only', () => {
    expect(coordinatorMethods()).toEqual(['EFECTIVO', 'TRANSFER'])
  })

  it('body source is MANUAL only in manual mode', () => {
    expect(isManualBodySource(true)).toBe('MANUAL')
    expect(isManualBodySource(false)).toBe('WEB')
  })
})
