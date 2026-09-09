import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    access: localStorage.getItem('access') || '',
    refresh: localStorage.getItem('refresh') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    merchantSlug: localStorage.getItem('merchantSlug') || 'ice-zone',
  }),
  getters: {
    isAuth: (s) => !!s.access,
    roles: (s): string[] => s.user?.roles ?? (s.user?.role ? [s.user.role] : []),
    isAdmin: (s): boolean => ((s.user?.roles ?? (s.user?.role ? [s.user.role] : [])) as string[]).includes('ADMIN'),
    merchantId: (s): number | null => s.user?.merchant_id ?? null,
    mustChange: (s): boolean => !!s.user?.must_change_password,
    hasAnyRole: (s) => (roles: string[]) => {
      const mine: string[] = s.user?.roles ?? (s.user?.role ? [s.user.role] : [])
      return roles.some((r) => mine.includes(r))
    },
  },
  actions: {
    setTokens(access: string, refresh: string) {
      this.access = access
      this.refresh = refresh
      localStorage.setItem('access', access)
      localStorage.setItem('refresh', refresh)
    },
    setUser(user: unknown) {
      this.user = user as never
      localStorage.setItem('user', JSON.stringify(user))
    },
    setMustChange(v: boolean) {
      if (this.user) {
        this.user = { ...(this.user as object), must_change_password: v } as never
        localStorage.setItem('user', JSON.stringify(this.user))
      }
    },
    clear() {
      this.access = ''
      this.refresh = ''
      this.user = null
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
      localStorage.removeItem('user')
    },
  },
})
