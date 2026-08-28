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
          primary: '#FACC15',
          secondary: '#38BDF8',
          accent: '#A78BFA',
          background: '#FFFbeb',
          surface: '#FFFFFF',
        },
      },
      dark: {
        colors: {
          primary: '#FACC15',
          secondary: '#38BDF8',
          accent: '#A78BFA',
          background: '#1c1917',
          surface: '#292524',
        },
      },
    },
  },
  defaults: {
    VBtn: { style: 'font-family: Comfortaa, sans-serif' },
  },
})
