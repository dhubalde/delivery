/** Navigate to an external URL (e.g. Mercado Pago checkout). Extracted so
 * tests can stub navigation without touching jsdom's location object. */
export function redirectTo(url: string): void {
  window.location.href = url
}
