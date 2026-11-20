import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import '@fontsource/comfortaa/400.css'
import '@fontsource/comfortaa/700.css'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import { componentDefaults, themes } from '@/design/tokens'

const stored = (() => {
  try { return localStorage.getItem('ice-zone-theme') as 'light' | 'dark' | null } catch { return null }
})()

// All visual decisions come from `@/design/tokens`; keep this file thin.
export default createVuetify({
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
  theme: {
    defaultTheme: stored === 'dark' ? 'dark' : 'light',
    themes: {
      light: { colors: themes.light },
      dark: { colors: themes.dark },
    },
  },
  defaults: componentDefaults,
})
