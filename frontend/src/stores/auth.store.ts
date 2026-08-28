import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    access: localStorage.getItem('access') || '',
    refresh: localStorage.getItem('refresh') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    merchantSlug: localStorage.getItem('merchantSlug') || 'zona-ice',
  }),
  getters: {
    isAuth: (s) => !!s.access,
    roles: (s): string[] => s.user?.roles ?? [],
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
