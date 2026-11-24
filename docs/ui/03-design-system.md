# 03 — Design system

Reglas visuales y componentes compartidos del panel. Toda vista nueva se arma
con estas piezas; no se estiliza Vuetify a mano.

## Principio

El diseño vive en **un solo lugar**. Si una decisión visual (color, densidad,
tipografía, orden de botones) está repetida en dos vistas, es un bug de
arquitectura: se mueve a `frontend/src/design/`.

```
frontend/src/design/
├── tokens.ts        # colores, densidad, defaults globales, tipografía
├── PageHeader.vue   # encabezado de página (título + subtítulo + acciones)
├── StatusChip.vue   # único render de estados booleanos
├── FormDialog.vue   # diálogo estándar de alta/edición e informativo
└── index.ts         # barrel: las vistas importan de `@/design`
```

```ts
import { PageHeader, DataTableCard, StatusChip, FormDialog } from '@/design'
```

## Tokens

`tokens.ts` es la fuente de verdad. `plugins/vuetify.ts` solo lo consume.

| Export | Qué define |
| --- | --- |
| `brandColors` | primary / secondary / accent de marca |
| `themes` | paletas `light` y `dark` completas |
| `statusColors` | semántica: `positive → success`, `negative → error`, `warning`, `neutral → default` |
| `componentDefaults` | defaults globales de Vuetify |
| `titleFont` | tipografía de títulos de página y diálogo |

Nunca escribir un hex, un `color="green"` ni un `density="compact"` suelto en una
vista. Se usa el token o el componente.

## Densidad

Los formularios son **dense**: entran en pantalla sin scroll.

```ts
const denseControl = { density: 'compact', hideDetails: 'auto' }
```

- `density: 'compact'` en TextField, Textarea, Select, Autocomplete, Combobox,
  FileInput, Switch y Checkbox (ya es default global).
- `hideDetails: 'auto'`: la clave. Reserva la línea de mensaje **solo** cuando
  hay hint o error visible. Con `true` se perdían los `persistent-hint`; con
  `false` los formularios crecían una línea por campo.
- Botones: `density="compact"` y nada más. **No** usar `size="small"` en botones
  de acción: encoge también la tipografía y rompe la consistencia.
  `size="small"` queda reservado para iconos dentro de tablas y toggles.

## Página

```vue
<PageHeader title="Productos" subtitle="Catálogo — precios, gustos y fotos">
  <v-btn color="primary" density="compact" prepend-icon="mdi-plus" @click="openCreate">
    Nuevo
  </v-btn>
</PageHeader>
```

Las acciones del slot se alinean solas a la derecha. Un `<h2>` suelto en una vista
es un error: siempre `PageHeader`.

## Tablas

Toda lista usa `DataTableCard`. Incluye buscador, contador `N de M`, orden por
click, paginado, estado de carga y mensaje de sin resultados.

```vue
<DataTableCard
  v-model:search="search"
  :headers="headers"
  :items="rows"
  :loading="loading"
  :total="total"
  no-data-text="Sin productos"
>
  <template #filters>
    <v-btn-toggle v-model="status" mandatory density="compact" variant="outlined" divided>
      <v-btn value="all" size="small">Todas</v-btn>
      <v-btn value="active" size="small">Activas</v-btn>
    </v-btn-toggle>
  </template>

  <template #item.is_active="{ item }">
    <StatusChip :value="Boolean(item.is_active)" positive="Activo" negative="Inactivo" />
  </template>

  <template #item.actions="{ item }">
    <v-btn icon="mdi-pencil" variant="text" size="small" density="compact" color="primary" title="Editar" @click="openEdit(item)" />
    <v-btn icon="mdi-delete" variant="text" size="small" density="compact" color="error" title="Desactivar" @click="askRemove(item)" />
  </template>
</DataTableCard>
```

Props: `headers`, `items`, `total`, `loading`, `itemValue`, `density`,
`itemsPerPage`, `noDataText`, `showCount`, `search` (v-model), `searchKeys`.
Slots: `filters`, `item.<key>`, `no-data`.

### Regla de `searchKeys`

- Filtrado **client-side** → pasar `search-keys` con los campos buscables.
- Filtrado **server-side** (la query ya manda `q`) → **no** pasar `search-keys`.
  Si se pasan, `v-data-table` refiltra el resultado del servidor y oculta
  coincidencias que el backend sí encontró.

### Formato de celdas

| Dato | Cómo se muestra |
| --- | --- |
| Booleano de estado | `StatusChip`, nunca un texto plano |
| Fecha/hora | `toLocaleString('es-AR')` |
| Dinero | `toLocaleString('es-AR', { minimumFractionDigits: 2 })` |
| Acciones | iconos de color: lápiz `primary`, llave `warning`, papelera `error`, sesiones `primary` |

## Estados

```vue
<StatusChip :value="Boolean(item.is_active)" positive="Activa" negative="Inactiva" />
<StatusChip :value="!item.is_closed" positive="Abierto" negative="Cerrado" negative-color="error" />
<StatusChip :value="session.active" positive="Activa" negative="Revocada" />
```

- Positivo = verde (`success`). Negativo = neutro por defecto.
- El negativo se pinta de `error` solo cuando cerrar/fallar es realmente un
  problema (por ejemplo una caja cerrada).
- **El verde tiene que significar algo.** Si todo es verde, nada es verde: los
  estados inactivos quedan neutros a propósito.
- Estados que no son booleanos (etapas de un pedido: `RECIBIDO`,
  `PREPARACION`, `ENTREGADO`) no son activo/inactivo y usan su propia paleta,
  no `StatusChip`.

## Diálogos

```vue
<FormDialog
  v-model="dlg"
  :title="editing ? 'Editar categoría' : 'Nueva categoría'"
  :loading="saving"
  :submit-disabled="!isAdmin"
  @submit="save"
>
  <v-text-field v-model="form.name" label="Nombre *" :error-messages="fieldErr('name')" />
  <v-switch v-model="form.is_active" label="Activa" color="primary" />
</FormDialog>
```

Props: `modelValue`, `title`, `submitLabel`, `cancelLabel`, `loading`,
`submitDisabled`, `hideSubmit`, `maxWidth` (default 520). Emits:
`update:modelValue`, `submit`, `close`.

Diálogo **informativo** (sesiones, token de reseteo, ticket): `hide-submit`,
`cancel-label`, y el botón propio en el slot `actions`.

```vue
<FormDialog v-model="sessDlg" :title="`Sesiones de ${user?.username}`" hide-submit cancel-label="Cerrar">
  <v-table density="compact" hover>…</v-table>
  <template #actions>
    <v-btn color="error" density="compact" @click="killSessions">Revocar todas</v-btn>
  </template>
</FormDialog>

<ConfirmDialog … />   <!-- confirmaciones destructivas: componente existente -->
```

Formularios largos: agrupar campos en `<v-row dense>` con dos columnas
(`sm="6"`) en vez de subir el `max-width`. Un diálogo de 640 px con dos
columnas entra en pantalla; uno de 640 px con una columna por campo no.

## Textos

Lo que escribe el usuario final va en español rioplatense, consistente con el
resto del panel ("Buscá, filtrá y ordená", "Nueva categoría"). El código,
nombres de props y comentarios van en inglés.

## Checklist de una vista nueva

- [ ] `PageHeader` con título, subtítulo y acciones.
- [ ] Listas con `DataTableCard`; filtros propios en el slot `filters`.
- [ ] Todo estado booleano con `StatusChip`.
- [ ] Diálogos con `FormDialog` (o `ConfirmDialog` si es destructivo).
- [ ] Sin `density`, `color`, hex ni `style` de fuente escritos a mano.
- [ ] Iconos de acción con color semántico y `size="small"`.
- [ ] Botones de acción con `density="compact"`, sin `size="small"`.
- [ ] Nada de `<h2>` sueltos ni tablas `<v-data-table>` crudas.

## Tests

`frontend/src/design/__tests__/design-system.spec.ts` es un guard: falla si
alguien saca `density: 'compact'`, cambia `hideDetails`, o rompe `StatusChip`,
`PageHeader` o `FormDialog`. Si un cambio visual es intencional, se actualiza el
spec en el mismo commit.

Los specs montan su propio `createVuetify()`, así que los defaults globales
**no** aplican en tests: se testea comportamiento, no apariencia.
