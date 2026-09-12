import { describe, it, expect, beforeEach } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'

function makeTestRouter() {
  // replicate routes from src/router/index.ts without file imports
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', redirect: '/ice-zone' },
      { path: '/login', component: { template: '<div>login</div>' } },
      { path: '/change-password', component: { template: '<div>cp</div>' }, meta: { requiresAuth: true } },
      {
        path: '/:slug',
        component: { template: '<div>public</div>' },
        children: [
          { path: '', name: 'catalog', component: { template: '<div>catalog</div>' } },
          { path: 'checkout', name: 'checkout', component: { template: '<div>checkout</div>' } },
          { path: 'my-orders', name: 'my-orders', component: { template: '<div>orders</div>' } },
        ],
      },
      { path: '/:pathMatch(.*)*', component: { template: '<div>notfound</div>' } },
    ],
  })
}

describe('slug routing', () => {
  let router: ReturnType<typeof makeTestRouter>
  beforeEach(() => {
    router = makeTestRouter()
  })

  it('routes /acme to catalog with slug param', async () => {
    await router.push('/acme')
    await router.isReady()
    const cur = router.currentRoute.value
    expect(cur.params.slug).toBe('acme')
    expect(cur.name).toBe('catalog')
  })

  it('routes /acme/checkout to checkout', async () => {
    await router.push('/acme/checkout')
    await router.isReady()
    const cur = router.currentRoute.value
    expect(cur.params.slug).toBe('acme')
    expect(cur.name).toBe('checkout')
  })

  it('routes /beta/my-orders to my-orders', async () => {
    await router.push('/beta/my-orders')
    await router.isReady()
    const cur = router.currentRoute.value
    expect(cur.params.slug).toBe('beta')
    expect(cur.name).toBe('my-orders')
  })

  it('/:slug isolates acme vs beta params', async () => {
    await router.push('/acme')
    expect(router.currentRoute.value.params.slug).toBe('acme')
    await router.push('/beta')
    expect(router.currentRoute.value.params.slug).toBe('beta')
  })

  it('root redirects to /ice-zone', async () => {
    await router.push('/')
    await router.isReady()
    expect(router.currentRoute.value.path).toBe('/ice-zone')
    expect(router.currentRoute.value.params.slug).toBe('ice-zone')
  })

  it('actual router file contains /:slug parent and NotFound fallback', async () => {
    const mod = await import('../index')
    const routes = (mod.default as any).getRoutes()
    const slugRoute = routes.find((r: any) => r.path === '/:slug')
    expect(slugRoute).toBeDefined()
    // vue-router flattens children — check named routes exist with slug param paths
    const catalog = routes.find((r: any) => r.name === 'catalog')
    const checkout = routes.find((r: any) => r.name === 'checkout')
    const myOrders = routes.find((r: any) => r.name === 'my-orders')
    expect(catalog).toBeDefined()
    expect(checkout).toBeDefined()
    expect(myOrders).toBeDefined()
    expect(catalog.path).toContain(':slug')
    expect(checkout.path).toContain(':slug')
    expect(myOrders.path).toContain(':slug')
    const notFound = routes.find((r: any) => r.path === '/:pathMatch(.*)*')
    expect(notFound).toBeDefined()
  })
})
