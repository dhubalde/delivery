import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import '@fontsource/comfortaa/400.css'
import '@fontsource/comfortaa/700.css'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'

const stored = (() => {
  try { return localStorage.getItem('ice-zone-theme') as 'light' | 'dark' | null } catch { return null }
})()

export default createVuetify({
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
          primary: '#06B6D4',
          secondary: '#64748B',
          accent: '#22D3EE',
          background: '#FAFAF8',
          surface: '#FFFFFF',
        },
      },
      dark: {
        colors: {
          primary: '#22D3EE',
          secondary: '#94A3B8',
          accent: '#22D3EE',
          background: '#1E293B',
          surface: '#334155',
        },
      },
    },
  },
  defaults: {
    VBtn: { style: 'font-family: Comfortaa, sans-serif', density: 'compact' },
    // Dense forms everywhere: compact controls, and messages only take vertical
    // space when there is something to show (hint with persistent-hint, or error).
    VTextField: { density: 'compact', hideDetails: 'auto' },
    VTextarea: { density: 'compact', hideDetails: 'auto' },
    VSelect: { density: 'compact', hideDetails: 'auto' },
    VAutocomplete: { density: 'compact', hideDetails: 'auto' },
    VCombobox: { density: 'compact', hideDetails: 'auto' },
    VFileInput: { density: 'compact', hideDetails: 'auto' },
    VSwitch: { density: 'compact', hideDetails: 'auto' },
    VCheckbox: { density: 'compact', hideDetails: 'auto' },
  },
})
