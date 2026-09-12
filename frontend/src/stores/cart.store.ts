import { defineStore } from 'pinia'
import { validate } from '@/utils/flavorPolicy'

type CartItem = { uid: string; product: any; qty: number; flavorIds: number[]; flavorNames: string[] }

export function cartKey(slug: string): string {
  return `cart:${slug}`
}

function readCart(slug: string): CartItem[] {
  try {
    const raw = localStorage.getItem(cartKey(slug))
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed as CartItem[]
  } catch {
    return []
  }
}

function writeCart(slug: string, items: CartItem[]): void {
  try {
    localStorage.setItem(cartKey(slug), JSON.stringify(items))
  } catch {}
}

export const useCartStore = defineStore('cart', {
  state: () => ({
    items: [] as CartItem[],
    _slug: '' as string,
    _hydratedSlug: '' as string,
  }),
  getters: {
    count: (s) => s.items.reduce((a, i) => a + i.qty, 0),
    total: (s) => s.items.reduce((a, i) => a + Number(i.product.price) * i.qty, 0),
    isEmpty: (s) => s.items.length === 0,
  },
  actions: {
    hydrate(slug: string): void {
      if (this._hydratedSlug === slug) return
      this._slug = slug
      this._hydratedSlug = slug
      this.items = readCart(slug)
    },
    setSlug(slug: string): void {
      this.hydrate(slug)
    },
    persist(): void {
      if (!this._slug) return
      writeCart(this._slug, this.items as CartItem[])
    },
    canAdd(product: any, flavorIds: number[]): string | null {
      const n = flavorIds.length
      if (product.min_flavors != null && product.max_flavors != null) {
        const min = product.min_flavors as number, max = product.max_flavors as number
        if (n < min || n > max) return min === max ? `Elige ${min} gustos` : `Elige ${min} a ${max} gustos`
        return null
      }
      return validate(product.pote_size ?? null, product.product_type, n)
    },
    add(product: any, flavorIds: number[], flavorNames: string[]) {
      const err = this.canAdd(product, flavorIds)
      if (err) throw new Error(err)
      this.items.push({ uid: crypto.randomUUID(), product, qty: 1, flavorIds: [...flavorIds], flavorNames: [...flavorNames] })
      this.persist()
    },
    remove(uid: string) {
      this.items = this.items.filter((i) => i.uid !== uid)
      this.persist()
    },
    inc(uid: string) {
      const it = this.items.find((i) => i.uid === uid)
      if (it) {
        it.qty++
        this.persist()
      }
    },
    dec(uid: string) {
      const it = this.items.find((i) => i.uid === uid)
      if (it) {
        it.qty = Math.max(1, it.qty - 1)
        this.persist()
      }
    },
    clear(slug?: string) {
      if (slug && slug !== this._slug) {
        try {
          localStorage.removeItem(cartKey(slug))
        } catch {}
        return
      }
      this.items = []
      this.persist()
    },
  },
})
