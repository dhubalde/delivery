import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', {
  state: () => ({
    theme: ((): 'light' | 'dark' => {
      try { return (localStorage.getItem('zona-ice-theme') as 'light' | 'dark') || 'light' } catch { return 'light' }
    })(),
    offline: !navigator.onLine,
  }),
  actions: {
    toggleTheme() {
      this.theme = this.theme === 'light' ? 'dark' : 'light'
      try { localStorage.setItem('zona-ice-theme', this.theme) } catch { /* ignore */ }
    },
    setOffline(v: boolean) { this.offline = v },
  },
})
