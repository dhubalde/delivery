import type { TicketOrder } from '@/api/panel/printing.api'

function esc(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

export function ticketWhen(order: TicketOrder): string {
  if (!order.created_at) return order.business_date
  return new Date(order.created_at).toLocaleString('es-AR', {
    timeZone: 'America/Argentina/Buenos_Aires',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const TICKET_CSS = `
  body { font-family: 'Courier New', monospace; font-size: 12px; width: 58mm; margin: 0 auto; padding: 4px; }
  h1 { font-size: 14px; text-align: center; margin: 0 0 2px; }
  .sub { text-align: center; margin: 0 0 6px; }
  table { width: 100%; border-collapse: collapse; }
  td { padding: 1px 0; vertical-align: top; }
  .r { text-align: right; white-space: nowrap; }
  .line { border-top: 1px dashed #000; margin: 4px 0; }
  .muted { color: #444; }
  .total { font-weight: bold; font-size: 13px; }
`

export function buildTicketHtml(order: TicketOrder, companyName: string): string {
  const flavors = (f: string[]) => (f && f.length ? ` <span class="muted">(${esc(f.join(', '))})</span>` : '')
  const payments = order.payments?.length
    ? order.payments.map((p) => `${esc(p.method)} ${esc(p.status)}`).join(' · ')
    : 'sin pagos'
  const items = order.items?.length
    ? order.items
        .map(
          (it) =>
            `<tr><td>${it.quantity}x ${esc(it.product_name)}${flavors(it.flavors)}</td><td class="r">${esc(it.line_total)}</td></tr>`,
        )
        .join('')
    : '<tr><td colspan="2" class="muted">sin items</td></tr>'
  return `
    <h1>${esc(companyName)}</h1>
    <p class="sub">Pedido #${esc(order.code)} — ${esc(order.state)}</p>
    <p class="sub muted">${esc(ticketWhen(order))}</p>
    <p>${esc(order.customer_name)}${order.customer_phone ? ` · ${esc(order.customer_phone)}` : ''}</p>
    ${order.address ? `<p class="muted">${esc(order.address)}</p>` : ''}
    <p class="muted">${esc(order.fulfillment)} · ${esc(order.source)}</p>
    <div class="line"></div>
    <table>${items}</table>
    <div class="line"></div>
    <table>
      <tr><td>Subtotal</td><td class="r">${esc(order.items_total)}</td></tr>
      ${Number(order.delivery_fee) ? `<tr><td>Envío</td><td class="r">${esc(order.delivery_fee)}</td></tr>` : ''}
      ${Number(order.discount) ? `<tr><td>Descuento</td><td class="r">-${esc(order.discount)}</td></tr>` : ''}
      <tr class="total"><td>TOTAL</td><td class="r">$${esc(order.total)}</td></tr>
      <tr><td colspan="2" class="muted">${payments}</td></tr>
    </table>
  `
}

export function printTicket(order: TicketOrder, companyName: string): void {
  const win = window.open('', '_blank', 'width=340,height=620')
  if (!win) return
  win.document.write(
    `<!doctype html><html><head><meta charset="utf-8"><title>Ticket #${esc(order.code)}</title><style>${TICKET_CSS}</style></head><body>${buildTicketHtml(order, companyName)}</body></html>`,
  )
  win.document.close()
  win.focus()
  win.print()
}
