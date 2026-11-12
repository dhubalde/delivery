import { describe, it, expect, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth.store'

describe('auth store merchantSlug', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('uses the merchant slug from the logged-in user', () => {
    const auth = useAuthStore()
    auth.setUser({
      username: 'admin_mlqc',
      role: 'ADMIN',
      merchant_id: 6,
      merchant_slug: 'mlqc',
      kind: 'COMPANY',
      must_change_password: false,
    })
    expect(auth.merchantSlug).toBe('mlqc')
  })

  it('falls back to ice-zone when the user has no merchant slug', () => {
    const auth = useAuthStore()
    auth.setUser({
      username: 'root',
      role: 'MASTER',
      merchant_id: null,
      kind: 'PERSONAL',
      must_change_password: false,
    })
    expect(auth.merchantSlug).toBe('ice-zone')
  })
})
