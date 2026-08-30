export function hasAnyRole(userRoles: string[], required: string[]): boolean {
  if (!required.length) return true
  return required.some((r) => userRoles.includes(r))
}

export const TRANSITION_ROLES: Record<string, string[]> = {
  'RECIBIDO->PREPARACION': ['TOMA_PEDIDOS', 'PREPARADOR', 'ADMIN'],
  'PREPARACION->FACTURACION': ['PREPARADOR', 'ADMIN'],
  'FACTURACION->LOGISTICA': ['CAJERO', 'ADMIN'],
  'LOGISTICA->ENTREGADO': ['REPARTIDOR', 'CAJERO', 'ADMIN'],
  'RECIBIDO->CANCELADO': ['TOMA_PEDIDOS', 'ADMIN'],
}

export const NEXT_STATE: Record<string, string> = {
  RECIBIDO: 'PREPARACION',
  PREPARACION: 'FACTURACION',
  FACTURACION: 'LOGISTICA',
  LOGISTICA: 'ENTREGADO',
}

export function nextStateOf(state: string): string | null {
  return NEXT_STATE[state] ?? null
}

export function requiredRolesFor(from: string, to: string): string[] {
  return TRANSITION_ROLES[`${from}->${to}`] ?? []
}

export function canAdvance(state: string, userRoles: string[], order?: { cash_declared?: boolean; payments?: { status: string; method: string }[]; fulfillment?: string }): { ok: boolean; reason: string } {
  const to = nextStateOf(state)
  if (!to) return { ok: false, reason: 'Estado terminal' }
  const required = requiredRolesFor(state, to)
  if (!hasAnyRole(userRoles, required)) return { ok: false, reason: `Requiere ${required.join(' o ')}` }
  if (state === 'PREPARACION' && !order?.cash_declared) return { ok: false, reason: 'Falta declarar efectivo' }
  if (state === 'FACTURACION') {
    const payments = order?.payments ?? []
    const hasPayment = payments.length > 0
    if (hasPayment) {
      const hasAnyPayment = payments.some((p) => p.status === 'CONFIRMED' || p.status === 'PENDING')
      if (!hasAnyPayment) return { ok: false, reason: 'Requiere al menos un pago' }
    }
  }
  return { ok: true, reason: '' }
}
