import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('@/layouts/PublicLayout.vue'), children: [{ path: '', component: () => import('@/views/CatalogView.vue') }, { path: 'checkout', component: () => import('@/views/CheckoutView.vue') }] },
    { path: '/panel', component: () => import('@/layouts/AdminLayout.vue'), meta: { requiresAuth: true }, children: [{ path: 'board', component: () => import('@/views/KanbanBoardView.vue') }, { path: 'dashboard', component: () => import('@/views/admin/AdminDashboardView.vue') }, { path: 'categories', component: () => import('@/views/admin/AdminCategoriesView.vue') }, { path: 'products', component: () => import('@/views/admin/AdminProductsView.vue') }, { path: 'flavors', component: () => import('@/views/admin/AdminFlavorsView.vue') }, { path: 'schedules', component: () => import('@/views/admin/AdminSchedulesView.vue') }, { path: 'delivery', component: () => import('@/views/admin/AdminDeliveryView.vue') }, { path: 'employees', component: () => import('@/views/admin/AdminEmployeesView.vue') }, { path: 'users', component: () => import('@/views/admin/AdminUsersView.vue') }, { path: 'cash-close', component: () => import('@/views/admin/AdminCashCloseView.vue') }, { path: 'merchant', component: () => import('@/views/admin/AdminMerchantView.vue') }, { path: 'contact', component: () => import('@/views/ContactView.vue') }, { path: 'catalog', redirect: '/panel/categories' }, { path: 'ops', redirect: '/panel/schedules' }] },
    { path: '/master', component: () => import('@/layouts/AdminLayout.vue'), meta: { requiresAuth: true, requiresPlatform: true }, children: [{ path: 'companies', component: () => import('@/views/master/MasterCompaniesView.vue') }, { path: 'users', component: () => import('@/views/master/MasterUsersView.vue') }, { path: 'audit', component: () => import('@/views/master/MasterAuditView.vue') }] },
    { path: '/login', component: () => import('@/views/LoginView.vue') },
    { path: '/change-password', component: () => import('@/views/ChangePasswordView.vue'), meta: { requiresAuth: true } },
    { path: '/:pathMatch(.*)*', component: () => import('@/views/NotFoundView.vue') },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuth) return '/login'
  if (to.meta.requiresPlatform && auth.merchantId !== null && !auth.hasAnyRole(['MASTER'])) return '/panel/board'
  if (auth.isAuth && auth.mustChange && to.path !== '/change-password' && to.path !== '/login') return '/change-password'
})

export default router
