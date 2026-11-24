---
name: delivery-design-system
description: Trigger — UI, vista, pantalla, tabla, listado, formulario, diálogo, panel, chip de estado, design system, frontend Vue. Build any delivery panel screen with the project's shared components instead of styling Vuetify by hand.
---

# Delivery design system

Every panel screen is composed from `frontend/src/design/`. Full rules and
snippets live in `docs/ui/03-design-system.md` — read it before writing a view.

## Load before work

1. `docs/ui/03-design-system.md` — rules, props, anti-patterns, checklist.
2. `frontend/src/design/tokens.ts` — the only source of colors and density.
3. The closest existing view as a reference, usually
   `frontend/src/views/master/MasterCompaniesView.vue`.

## Non-negotiable rules

- Import from `@/design` (`PageHeader`, `DataTableCard`, `StatusChip`,
  `FormDialog`). Never `@/components/DataTableCard.vue` in new code.
- Page header: `PageHeader` with `title`, `subtitle` and action buttons in the
  default slot. No bare `<h2>`.
- Lists: `DataTableCard` with `headers`, `items`, `loading`, `total`; extra
  filters go in the `#filters` slot.
- `search-keys` only for client-side filtering. Server-filtered views (the query
  already sends `q`) must not pass it, or the table hides real matches.
- States: `StatusChip`. Positive is green (`success`), negative is neutral by
  default, `negative-color="error"` only when failing is genuinely a problem.
  Non-boolean stages (order kanban) keep their own palette.
- Dialogs: `FormDialog`; `hide-submit` + `#actions` for informational dialogs;
  `ConfirmDialog` for destructive confirmations.
- Buttons: `density="compact"` only. Never `size="small"` on action buttons;
  `size="small"` is for table action icons and status toggles.
- Action icons carry color: pencil `primary`, key `warning`, trash `error`,
  sessions `primary`.
- Never hardcode a hex, `color="green"`, `density`, or a font-family inline.
  If a visual decision repeats twice, move it into `design/`.

## Workflow

1. Read the doc and the reference view.
2. Write the view using the components; add tests next to the existing specs.
3. Run `npx vitest run` and `npm run build` (vue-tsc) from `frontend/`.
4. If the visual change is intentional and breaks
   `src/design/__tests__/design-system.spec.ts`, update the spec in the same
   commit.

## Failure modes seen before

- Adding `search-keys` to a server-filtered table hides matches.
- `size="small"` on action buttons shrinks the typography and breaks the row.
- Type annotations inside Vue template expressions break `vue-tsc` (TS1005);
  move helpers to the script block.
- Props typed with an index signature (`Record<string, unknown>`) reject typed
  arrays; declare `items: unknown[]`.
- Specs mount their own `createVuetify()`, so global defaults do not apply in
  tests: assert behavior, not appearance.
