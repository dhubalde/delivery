import { defineStore } from 'pinia'
import { validateForProduct } from '@/utils/flavorPolicy'
type CartItem = { uid: string; product: any; qty: number; flavorIds: number[]; flavorNames: string[] }
export const useCartStore = defineStore('cart', {
  state: () => ({ items: [] as CartItem[] }),
  getters: {
    count: (s) => s.items.reduce((a, i) => a + i.qty, 0),
    total: (s) => s.items.reduce((a, i) => a + Number(i.product.price) * i.qty, 0),
    isEmpty: (s) => s.items.length === 0,
  },
  actions: {
    canAdd(product: any, flavorIds: number[]): string | null {
      return validateForProduct(product, flavorIds.length)
    },
    add(product: any, flavorIds: number[], flavorNames: string[]) {
      const err = this.canAdd(product, flavorIds)
      if (err) throw new Error(err)
      this.items.push({ uid: crypto.randomUUID(), product, qty: 1, flavorIds: [...flavorIds], flavorNames: [...flavorNames] })
    },
    remove(uid: string) { this.items = this.items.filter((i) => i.uid !== uid) },
    inc(uid: string) { const it = this.items.find((i) => i.uid === uid); if (it) it.qty++ },
    dec(uid: string) { const it = this.items.find((i) => i.uid === uid); if (it) it.qty = Math.max(1, it.qty - 1) },
    clear() { this.items = [] },
  },
})
