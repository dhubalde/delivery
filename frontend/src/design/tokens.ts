/**
 * Single source of truth for the product's visual language.
 *
 * Every global decision lives here: theme colors, control density and the
 * semantic colors used by status chips. Views must not hardcode colors or
 * densities; they compose the components in `src/design/`.
 */

export const brandColors = {
  primary: '#06B6D4',
  secondary: '#64748B',
  accent: '#22D3EE',
} as const

export const themes = {
  light: {
    primary: brandColors.primary,
    secondary: brandColors.secondary,
    accent: brandColors.accent,
    background: '#FAFAF8',
    surface: '#FFFFFF',
  },
  dark: {
    primary: '#22D3EE',
    secondary: '#94A3B8',
    accent: '#22D3EE',
    background: '#1E293B',
    surface: '#334155',
  },
} as const

/**
 * Semantic colors. `positive` is the green every "active/ok" state uses;
 * `neutral` is deliberately gray so a green chip always means something.
 */
export const statusColors = {
  positive: 'success',
  negative: 'error',
  warning: 'warning',
  neutral: 'default',
} as const

/** Form controls: one dense line each, message space only when there is a message. */
const denseControl = { density: 'compact', hideDetails: 'auto' } as const

export const componentDefaults = {
  VBtn: { style: 'font-family: Comfortaa, sans-serif', density: 'compact' },
  VTextField: denseControl,
  VTextarea: denseControl,
  VSelect: denseControl,
  VAutocomplete: denseControl,
  VCombobox: denseControl,
  VFileInput: denseControl,
  VSwitch: denseControl,
  VCheckbox: denseControl,
  VDataTable: { density: 'comfortable' },
} as const

/** Font used by page and dialog titles. */
export const titleFont = 'Comfortaa, sans-serif'
