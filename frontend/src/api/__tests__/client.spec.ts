import { describe, it, expect, beforeEach } from 'vitest'
import { customerKey } from '@/stores/customer.store'

// We test the header attachment helper behavior indirectly via localStorage keys
// and extractPublicSlug logic duplicated from client.ts
function extractPublicSlug(url?: string): string | null {
  if (!url) return null
  const m = url.match(/\/public\/([^\/\?#]+)/)
  if (m && m[1]) return decodeURIComponent(m[1])
  return null
}

function getCustomerAccessForSlug(slug: string): string | null {
  try {
    const raw = localStorage.getItem(customerKey(slug))
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (parsed?.tokens) return parsed.tokens.access || parsed.access || null
    return parsed?.access || null
  } catch {
    return null
  }
}

describe('api client Customer header', () => {
  beforeEach(() => localStorage.clear())

  it('extracts slug from /public/<slug>/...', () => {
    expect(extractPublicSlug('/api/public/acme/catalog')).toBe('acme')
    expect(extractPublicSlug('/api/public/beta/orders')).toBe('beta')
    expect(extractPublicSlug('/api/public/acme/customers/me')).toBe('acme')
    expect(extractPublicSlug('/api/v1/orders')).toBeNull()
  })

  it('reads Customer token only for matching slug', () => {
    localStorage.setItem(customerKey('acme'), JSON.stringify({ access: 'tok-acme', refresh: '' }))
    expect(getCustomerAccessForSlug('acme')).toBe('tok-acme')
    expect(getCustomerAccessForSlug('beta')).toBeNull()
  })

  it('two slugs have independent Customer headers', () => {
    localStorage.setItem(customerKey('acme'), JSON.stringify({ access: 'tok-acme', refresh: '' }))
    localStorage.setItem(customerKey('beta'), JSON.stringify({ access: 'tok-beta', refresh: '' }))
    expect(getCustomerAccessForSlug('acme')).toBe('tok-acme')
    expect(getCustomerAccessForSlug('beta')).toBe('tok-beta')
    // simulate request to acme orders -> should attach acme token, not beta
    const slug = extractPublicSlug('/api/public/acme/orders')
    expect(slug).toBe('acme')
    expect(getCustomerAccessForSlug(slug!)).toBe('tok-acme')
    expect(getCustomerAccessForSlug(slug!)).not.toBe('tok-beta')
  })
})
