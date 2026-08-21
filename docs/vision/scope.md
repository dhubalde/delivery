# MVP Scope — Delivery Multi-Commerce Platform

## In Scope (MVP — Ice Cream Shop Vertical)

### Core Platform

| Capability | Description |
|------------|-------------|
| **Multi-merchant architecture** | Each merchant has isolated configuration, catalog, orders, employees, and closure |
| **Merchant onboarding** | Self-service registration → business config → catalog → schedules → payments → delivery → go live |
| **Role-based access** | 5 roles (Admin, Cashier, Preparer, Courier, Order Taker) with multi-role assignment per employee |
| **Web customer portal** | Public, no-registration ordering from mobile browser — PWA-ready |

### Catalog Management (Configurable per Merchant)

| Entity | Configuration |
|--------|---------------|
| **Categories** | Unlimited, merchant-defined (e.g., "Potes", "Bombones", "Tortas", "Conos") |
| **Products** | Name, description, price, category, active flag |
| **Flavors (gustos)** | Global flavor list per merchant; assigned to products that require them |
| **Product-Flavor Rules** | **Potes**: 1kg/1/2kg → 3-4 flavors required; 1/4kg → 2-3 flavors required. **Bombones, Tortas, Conos** → unit, no flavors |

### Order Channels & Intake

- **Web ordering** — mobile-first, no login, guest checkout
- **Real-time order reception** — kitchen screen + auto-print ticket
- **Business hours enforcement** — configurable per day (Mon-Sun), multiple time ranges per day (e.g., Sat 00:01-01:00 + 09:00-00:00). Closed = ordering blocked, "Cerrado" banner shown

### Fulfillment Modes (Both from Day 1)

| Mode | Description |
|------|-------------|
| **Delivery a domicilio** | Courier assigned, route sheet, proof of delivery |
| **Retiro en local** | Customer picks up; order moves through same states minus courier leg |

### Payment Methods (Mixed)

| Method | Flow | Accounting |
|--------|------|------------|
| **Efectivo (Cash)** | Declared at order → collected at door (delivery) or counter (pickup) → courier returns cash → cashier registers receipt → cash total updates | Pending (blinking) until cashier confirms receipt |
| **Billetera virtual / Tarjetas** | Online payment at checkout via gateway (e.g., MercadoPago) → immediate confirmation | Settled instantly, added to method total |

### Delivery Configuration (3 Dimensions, Per Merchant)

| Dimension | Options |
|-----------|---------|
| **Modo** | `propio` (own fleet) / `tercerizado` (third-party) |
| **Cobro** | `en_pedido` (included in order total) / `en_entrega` (courier collects) |
| **Cálculo** | `por_zona` / `fijo` / `gratis_monto` (free over threshold) / `por_distancia` |

**Accounting Rule**: `tercerizado` + `en_pedido` → delivery fee is **passthrough** (not merchant revenue). Shown separately on ticket, recorded for courier settlement.

### Order State Machine (Card States)

| State | Color | Trigger | Key Actions |
|-------|-------|---------|-------------|
| **RECIBIDO** | 🟡 Yellow | Customer confirms | Print ticket, show on kitchen screen |
| **PREPARACIÓN** | 🔵 Blue | Ticket printed / "Start prep" | Flavor selection UI, "Terminado" button |
| **FACTURACIÓN** | 🟢 Green | Preparer marks done | Ticket + payment method. Cash = blinking (pending); Digital = fixed |
| **LOGÍSTICA** | 🔴 Red | Billing complete | Assign courier, route sheet |
| **ENTREGADO** | 🏁 Logo | Courier confirms delivery | If cash: courier returns → cashier receives → blinking stops → cash total increments |

### Cancellation

- **Allowed**: Only in `RECIBIDO` (yellow) state
- **Blocked**: Once order enters `PREPARACIÓN` (blue)
- **Tracking**: Cancelled orders counted separately → **TOTAL RECHAZADOS** in daily closure

### Daily Cash Closing (Cierre de Caja)

Automated printed ticket with:
- **EFECTIVO** — total cash confirmed received
- **BILLETERAS VIRTUALES** — total digital wallet payments
- **TARJETAS** — total card payments
- **TOTAL ENTREGADOS** — delivered orders count
- **TOTAL RECHAZADOS** — cancelled orders count

### Notifications (Foundational)

- **Cashier alerts**: Pending cash collections from couriers
- **Sector task notifications**: Prep, billing, logistics queues

---

## Out of Scope (Phase 2+)

| Feature | Reason |
|---------|--------|
| **Native mobile apps** (iOS/Android) | Web PWA covers MVP; apps add store friction |
| **Customer registration / accounts** | Guest checkout is faster for impulse food orders |
| **Geolocation / radius-based delivery** | Merchant defines zones manually in MVP |
| **Advanced analytics dashboard** | Daily closure ticket is the MVP insight; dashboards later |
| **Multi-location / franchise management** | Single-locus MVP first |
| **Inventory management / stock deduction** | Not required for ice cream MVP (made-to-order) |
| **Loyalty / promotions engine** | Configurable discounts later |
| **POS hardware integration** | Cash drawer, receipt printer — later |
| **Courier app / GPS tracking** | Web route sheet sufficient for MVP |
| **Marketplace / aggregator features** | This is *merchant-owned* channel, not a marketplace |
| **Multi-language / i18n** | Spanish-first MVP |
| **Automated courier settlement / payouts** | Manual recording in MVP |
| **Kitchen display system (KDS) hardware** | Web screen + print is MVP |