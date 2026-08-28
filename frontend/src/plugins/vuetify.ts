import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import '@fontsource/comfortaa/400.css'
import '@fontsource/comfortaa/700.css'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'

const stored = (() => {
  try { return localStorage.getItem('ice-zone-theme') as 'light' | 'dark' | null } catch { return null }
})()

  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
  theme: {
    defaultTheme: stored === 'dark' ? 'dark' : 'light',
    themes: {
      light: {
        colors: {
          primary: '#06B6D4', // turquesa más azulado
          secondary: '#64748B', // gris
          accent: '#22D3EE',
          background: '#FAFAF8', // blanco tiza
          surface: '#FFFFFF',
        },
      },
      dark: {
        colors: {
          primary: '#22D3EE', // turquesa azulado claro para dark
          secondary: '#94A3B8',
          accent: '#22D3EE',
          background: '#1E293B', // slate oscuro
          surface: '#334155',
        },
      },
    },
  },
  defaults: {
    VBtn: { style: 'font-family: Comfortaa, sans-serif' },
  },
