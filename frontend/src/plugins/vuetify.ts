import 'vuetify/styles'
import '@fontsource/comfortaa/400.css'
import '@fontsource/comfortaa/700.css'
import { createVuetify } from 'vuetify'

const stored = (() => {
  try { return localStorage.getItem('zona-ice-theme') as 'light' | 'dark' | null } catch { return null }
})()

export default createVuetify({
  theme: {
    defaultTheme: stored === 'dark' ? 'dark' : 'light',
    themes: {
      light: {
        colors: {
          primary: '#14B8A6', // turquesa
          secondary: '#64748B', // gris
          accent: '#5EEAD4',
          background: '#FAFAF8', // blanco tiza
          surface: '#FFFFFF',
        },
      },
      dark: {
        colors: {
          primary: '#2DD4BF', // turquesa claro para dark
          secondary: '#94A3B8',
          accent: '#5EEAD4',
          background: '#1E293B', // slate oscuro
          surface: '#334155',
        },
      },
    },
  },
  defaults: {
    VBtn: { style: 'font-family: Comfortaa, sans-serif' },
  },
})
