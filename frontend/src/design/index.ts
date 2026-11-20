/**
 * Design system entry point.
 *
 * New views import from `@/design` instead of styling Vuetify by hand:
 *
 *   import { PageHeader, DataTableCard, StatusChip, FormDialog } from '@/design'
 *
 * Rules live in `docs/design-system.md`.
 */
export { default as PageHeader } from './PageHeader.vue'
export { default as StatusChip } from './StatusChip.vue'
export { default as FormDialog } from './FormDialog.vue'
export { default as DataTableCard } from '@/components/DataTableCard.vue'
export { brandColors, themes, statusColors, componentDefaults, titleFont } from './tokens'
