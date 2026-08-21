# Business Rules — Delivery Multi-Commerce Platform

> **Source of truth** for all domain invariants. Every rule here must be enforced in code (domain layer) and tested. Rules are merchant-scoped unless noted.

---

## 1. Catalog & Flavor Rules

| Rule ID | Rule | Enforcement Point |
|---------|------|-------------------|
| **BR-CAT-01** | A product belongs to exactly one category. Categories are merchant-defined. | Domain: `Product.category_id` required, FK to `Category` |
| **BR-CAT-02** | Flavors are global per merchant. A flavor can be assigned to multiple products. | Domain: `Flavor.merchant_id`, `ProductFlavor` join table |
| **BR-CAT-03** | **Pote products** (1kg, 1/2kg, 1/4kg) **require flavor selection** at cart/add-to-order time. | API: `POST /cart/items` validates `flavor_ids` present |
| **BR-CAT-04** | **1kg / 1/2kg potes** → minimum 3 flavors, maximum 4 flavors. | Domain: `PoteFlavorPolicy.validate(flavor_ids)` |
| **BR-CAT-05** | **1/4kg potes** → minimum 2 flavors, maximum 3 flavors. | Domain: `PoteFlavorPolicy.validate(flavor_ids)` |
| **BR-CAT-06** | **Unit products** (bombones, tortas, conos) → **zero flavors allowed**. Adding flavors = error. | Domain: `UnitProductPolicy.validate(flavor_ids)` → must be empty |
| **BR-CAT-07** | Flavor stock is not tracked in MVP (made-to-order). | N/A — documented for future |

---

## 2. Business Hours & Order Blocking

| Rule ID | Rule | Enforcement Point |
|---------|------|-------------------|
| **BR-HRS-01** | Schedule defined per day (Mon–Sun). Each day supports **multiple time ranges** (e.g., `00:01-01:00`, `09:00-00:00`). | Domain: `Schedule.day_of_week`, `Schedule.time_ranges[]` |
| **BR-HRS-02** | If current time **outside all ranges** for today → ordering **blocked**. Web shows "Cerrado" banner, no checkout. | API: `GET /menu` returns `closed: true` + `next_open_at` |
| **BR-HRS-03** | Schedule changes take effect **immediately** for new orders. In-progress orders continue. | API: no versioning on schedule; read-at-request-time |
| **BR-HRS-04** | Timezone = merchant's configured timezone (default: America/Argentina/Buenos_Aires). | Config: `Merchant.timezone` |

---

## 3. Order State Machine (Card States)

| Rule ID | Rule | Enforcement Point |
|---------|------|-------------------|
| **BR-ORD-01** | Valid transitions only: `RECIBIDO → PREPARACIÓN → FACTURACIÓN → LOGÍSTICA → ENTREGADO` | Domain: `OrderStateMachine.can_transition(from, to)` |
| **BR-ORD-02** | **Cancellation allowed ONLY in `RECIBIDO`**. Any other state → rejection. | API: `POST /orders/{id}/cancel` checks `state == RECIBIDO` |
| **BR-ORD-03** | Cancelled orders increment **TOTAL RECHAZADOS** (not ENTREGADOS). | Domain: `Order.cancel()` sets `cancelled_at`, `rejected: true` |
| **BR-ORD-04** | `RECIBIDO → PREPARACIÓN` triggered by **ticket print** or explicit "Iniciar preparación". | Event: `TicketPrinted` or `PreparationStarted` |
| **BR-ORD-05** | `PREPARACIÓN → FACTURACIÓN` triggered by preparer pressing **"Terminado"**. | API: `POST /orders/{id}/complete-prep` |
| **BR-ORD-06** | `FACTURACIÓN → LOGÍSTICA` automatic when billing confirmed (payment method recorded). | Domain: `BillingConfirmed` event |
| **BR-ORD-07** | `LOGÍSTICA → ENTREGADO` triggered by courier **confirming delivery**. | API: `POST /orders/{id}/deliver` (courier role) |
| **BR-ORD-08** | **Retiro en local** skips `LOGÍSTICA` → goes `FACTURACIÓN → ENTREGADO` on customer pickup confirmation. | Domain: `FulfillmentType.PICKUP` bypasses logistics |

---

## 4. Mixed Payments & Cash Asynchrony

| Rule ID | Rule | Enforcement Point |
|---------|------|-------------------|
| **BR-PAY-01** | Order declares **payment method(s)** at checkout: `EFECTIVO`, `BILLETERA`, `TARJETA`. Multiple allowed (split). | API: `POST /orders` body includes `payments: [{method, amount}]` |
| **BR-PAY-02** | **Digital payments** (billetera/tarjeta) → processed synchronously via gateway. Order only confirms if gateway succeeds. | Integration: `PaymentGateway.charge()` before `Order.create()` |
| **BR-PAY-03** | **Cash (efectivo)** → **asynchronous**. Amount declared at order → status `PENDING` (blinking in UI). | Domain: `CashPayment.status = PENDING` |
| **BR-PAY-04** | Cash **collected by courier** (delivery) or **at counter** (pickup). Courier returns cash → cashier **confirms receipt**. | API: `POST /cash/collections` (cashier role) |
| **BR-PAY-05** | Cashier confirmation → cash payment status `CONFIRMED` → blinking stops → added to **EFECTIVO total** in closure. | Domain: `CashPayment.confirm()` |
| **BR-PAY-06** | **No partial cash confirmation**. Full declared amount or nothing. | Domain: `CashPayment.confirm(amount)` validates `amount == declared` |
| **BR-PAY-07** | Cash discrepancy (courier returns less) → **manual adjustment** by admin, logged with reason. | Admin API: `POST /cash/adjustments` |
| **BR-PAY-08** | Payment totals per method **immutable after confirmation**. Corrections = new adjustment record. | Domain: `PaymentConfirmed` event is append-only |

---

## 5. Delivery Configuration (3 Dimensions)

| Rule ID | Rule | Enforcement Point |
|---------|------|-------------------|
| **BR-DEL-01** | **Modo**: `PROPIO` (own fleet) or `TERCERIZADO` (third-party). Per merchant. | Config: `MerchantDeliveryConfig.mode` |
| **BR-DEL-02** | **Cobro**: `EN_PEDIDO` (included in order total) or `EN_ENTREGA` (courier collects). Per merchant. | Config: `MerchantDeliveryConfig.charge_mode` |
| **BR-DEL-03** | **Cálculo**: `POR_ZONA`, `FIJO`, `GRATIS_MONTO` (free over threshold), `POR_DISTANCIA`. Per merchant. | Config: `MerchantDeliveryConfig.calculation` + params |
| **BR-DEL-04** | **Passthrough Accounting Rule**: If `mode == TERCERIZADO` AND `charge_mode == EN_PEDIDO` → delivery fee is **NOT merchant revenue**. | Domain: `DeliveryFee.is_passthrough()` |
| **BR-DEL-05** | Passthrough fee → shown **separately on ticket** (not in subtotal). Recorded for **courier settlement**. | Template: `TicketRenderer.render_delivery_passthrough()` |
| **BR-DEL-06** | If `mode == PROPIO` → delivery fee is **merchant revenue** (part of total). | Domain: `DeliveryFee.is_revenue()` |
| **BR-DEL-07** | If `charge_mode == EN_ENTREGA` → fee collected by courier at door (cash or card per courier capability). Not in order total. | Domain: `Order.delivery_fee_charged_at = DELIVERY` |

---

## 6. Roles & Multi-Role Employees

| Rule ID | Rule | Enforcement Point |
|---------|------|-------------------|
| **BR-ROL-01** | 5 base roles: `ADMIN`, `CAJERO`, `PREPARADOR`, `REPARTIDOR`, `TOMA_PEDIDOS`. | Enum: `EmployeeRole` |
| **BR-ROL-02** | Employee can have **multiple roles simultaneously**. Permissions = union of roles. | Domain: `Employee.roles[]` → `PermissionSet.union()` |
| **BR-ROL-03** | Role assignment by **Admin only**. | API: `POST /employees/{id}/roles` requires `ADMIN` |
| **BR-ROL-04** | **Off-peak**: single employee holds all roles → full workflow access. | UI: role-based navigation shows all sections |
| **BR-ROL-05** | **Admin** = only role that can: configure merchant, close cash, view analytics, manage employees. | Permission matrix |
| **BR-ROL-06** | **Cajero** = only role that can: confirm cash receipts, print closure ticket, issue invoices. | Permission matrix |
| **BR-ROL-07** | **Preparador** = only role that can: mark order "Terminado" (PREPARACIÓN → FACTURACIÓN). | Permission matrix |
| **BR-ROL-08** | **Repartidor** = only role that can: view route sheet, mark "Entregado". | Permission matrix |
| **BR-ROL-09** | **Toma Pedidos** = only role that can: manually create/edit orders from phone/WhatsApp. | Permission matrix |

---

## 7. Daily Cash Closing (Cierre de Caja)

| Rule ID | Rule | Enforcement Point |
|---------|------|-------------------|
| **BR-CIE-01** | Closure **only by Admin**. Generates printed ticket + immutable record. | API: `POST /cash/close` requires `ADMIN` |
| **BR-CIE-02** | Ticket includes: **EFECTIVO**, **BILLETERAS VIRTUALES**, **TARJETAS**, **TOTAL ENTREGADOS**, **TOTAL RECHAZADOS**. | Domain: `CashClosure.calculate_totals()` |
| **BR-CIE-03** | **EFECTIVO** = sum of all `CashPayment` with `status == CONFIRMED` for the day. | Query: `SUM(amount) WHERE confirmed_at BETWEEN day_start AND day_end` |
| **BR-CIE-04** | **BILLETERAS VIRTUALES** = sum of confirmed digital wallet payments. | Query: `SUM(amount) WHERE method = BILLETERA AND status = CONFIRMED` |
| **BR-CIE-05** | **TARJETAS** = sum of confirmed card payments. | Query: `SUM(amount) WHERE method = TARJETA AND status = CONFIRMED` |
| **BR-CIE-06** | **TOTAL ENTREGADOS** = count of orders with `state == ENTREGADO` and `delivered_at` today. | Query: `COUNT(*) WHERE state = ENTREGADO AND delivered_at IN today` |
| **BR-CIE-07** | **TOTAL RECHAZADOS** = count of orders with `cancelled_at` today (only from RECIBIDO). | Query: `COUNT(*) WHERE cancelled_at IN today` |
| **BR-CIE-08** | Closure **locks the day** — no new orders can be backdated to closed day. | Domain: `Order.create()` rejects if `business_date <= last_closure_date` |
| **BR-CIE-09** | **Re-opening** a closed day = Admin action, creates audit log, requires reason. | Admin API: `POST /cash/reopen` |

---

## 8. Notifications (Foundational Rules)

| Rule ID | Rule | Enforcement Point |
|---------|------|-------------------|
| **BR-NOT-01** | **Cashier alert** when courier departs with cash order → "Efectivo pendiente: $X, Pedido #Y". | Event: `CourierDepartedWithCash` → `NotificationService.alert_cashiers()` |
| **BR-NOT-02** | **Sector task notification**: Preparador sees new `PREPARACIÓN` orders; Cajero sees `FACTURACIÓN` queue; Repartidor sees `LOGÍSTICA` assignments. | Real-time: WebSocket channels per role/sector |
| **BR-NOT-03** | Notifications **persist until acknowledged** or order leaves sector. | Domain: `Notification.dismiss()` on state transition |

---

## 9. Cross-Cutting Invariants

| Rule ID | Rule | Enforcement Point |
|---------|------|-------------------|
| **BR-X-01** | **Tenant isolation**: All queries scoped to `merchant_id`. Zero cross-merchant data access. | Middleware: `TenantContext.current_merchant_id` injected in all repositories |
| **BR-X-02** | **Idempotency**: Order creation, payment confirmation, cash collection — all idempotent via `idempotency_key`. | API: `Idempotency-Key` header required for mutating endpoints |
| **BR-X-03** | **Audit trail**: Every state change, payment, cash movement, config change → immutable event log. | Event Store: `EventStore.append(event)` |
| **BR-X-04** | **Soft deletes only**: No hard deletes on orders, payments, products, employees. | Domain: `deleted_at` timestamp, filtered by default |
| **BR-X-05** | **Currency**: ARS (Argentine Peso). All amounts stored as integer cents (`monto_centavos`). | Domain: `Money` value object, `amount_cents: int` |

---

## Rule Change Process

1. **Propose** → Add row to this table with `PROPOSED` status
2. **Review** → Architect + Domain Expert sign-off
3. **Implement** → Code + tests + migration
4. **Verify** → `sdd-verify` confirms rule enforced
5. **Promote** → Status → `ACTIVE`

> This document is the **single source of truth** for business rules. If code behaves differently, code is wrong.