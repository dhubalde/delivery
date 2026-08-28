export const qk = {
  menu: (slug: string) => ['menu', slug] as const,
  products: (p: { slug: string; category?: number; search?: string }) => ['products', p] as const,
  flavors: (p: { slug: string; category?: number; search?: string }) => ['flavors', p] as const,
  ordersBoard: (p: { state: string; businessDate: string }) => ['orders', 'board', p] as const,
  forecast: (p: { days: 5 }) => ['weather', 'forecast', p] as const,
}
