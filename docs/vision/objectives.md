# MVP Objectives — Delivery Multi-Commerce Platform

## Measurable Success Metrics

### Operational Efficiency

| Objective | Metric | Target | Measurement Method |
|-----------|--------|--------|-------------------|
| **Order processing reliability** | Orders processed end-to-end without manual intervention | ≥ 99.5% | Automated audit: order state transitions match expected flow |
| **Daily closure accuracy** | Cash closing ticket matches actual payments received | 100% (zero variance) | End-of-day reconciliation: system totals = physical cash + gateway reports |
| **Preparation time visibility** | Average time from RECIBIDO → PREPARACIÓN → FACTURACIÓN | < 15 min (ice cream) | Timestamp diff per order; dashboard percentile (p50, p90) |
| **Courier cash tracking** | Cash declared at order = cash confirmed received by cashier | 100% traceability | Audit trail: order.cash_declared → courier.collection → cashier.confirmation |

### Merchant Onboarding & Configuration

| Objective | Metric | Target | Measurement Method |
|-----------|--------|--------|-------------------|
| **Time to first order** | Merchant registration → live ordering | < 30 minutes | Stopwatch test with sample merchant |
| **Catalog configuration completeness** | Products with required flavor rules configured | 100% of active products | Validation: potes have min/max flavors; unit items have zero |
| **Schedule coverage** | Business hours defined for all 7 days | 100% days covered | Config audit: no gaps unless intentionally closed |

### Customer Experience

| Objective | Metric | Target | Measurement Method |
|-----------|--------|--------|-------------------|
| **Order completion rate** | Started checkout → confirmed order | ≥ 85% | Funnel analytics: cart → payment → confirmation |
| **Mobile web performance** | Time to interactive (TTI) on 3G | < 3 seconds | Lighthouse CI / Web Vitals |
| **Order placement time** | Land on menu → confirm order | < 2 minutes | User testing + analytics |
| **Error-free checkout** | Payment failures due to system (not gateway) | < 0.5% | Error tracking: payment_intent_failed (system) vs gateway_declined |

### Employee Workflow

| Objective | Metric | Target | Measurement Method |
|-----------|--------|--------|-------------------|
| **Role-switching fluidity** | Employee changes role mid-shift without re-login | Supported | E2E test: same user token, different role permissions |
| **Kitchen screen latency** | Order appears on prep screen after customer confirms | < 2 seconds | WebSocket/message bus latency measurement |
| **Ticket print reliability** | Auto-print on RECIBIDO | 100% | Print queue monitoring |
| **Cashier pending-cash visibility** | Blinking cash orders visible within 5s of courier departure | 100% | Real-time sync test |

### Technical Quality

| Objective | Metric | Target | Measurement Method |
|-----------|--------|--------|-------------------|
| **API reliability** | 5xx error rate on order-critical endpoints | < 0.1% | APM / logging |
| **State machine integrity** | Invalid state transitions prevented | 100% | Integration tests: all invalid transitions return 409 |
| **Concurrency safety** | Simultaneous cashier confirmations for same cash order | No double-count | Load test: 10 concurrent confirmations → 1 recorded |
| **Data isolation** | Merchant A never sees Merchant B data | 100% | Tenant isolation tests (row-level security) |

## Non-Functional Requirements

| Category | Requirement | Validation |
|----------|-------------|------------|
| **Availability** | 99.9% uptime during business hours | SLA monitoring |
| **Scalability** | Support 50 concurrent orders per merchant | Load test |
| **Security** | PCI DSS SAQ-A for card data (gateway handles PAN) | Annual audit |
| **Privacy** | No PII stored beyond order minimum (name, phone, address) | Data map review |
| **Auditability** | Immutable order event log (state changes, payments, user actions) | Event store verification |

## Definition of Done (MVP Launch)

- [ ] All **In Scope** features from `scope.md` implemented and tested
- [ ] All **Objectives** above measurable and verified in staging
- [ ] Daily closure ticket prints correctly for 5 consecutive simulated days
- [ ] Cash flow: customer pays cash → courier collects → cashier confirms → totals match
- [ ] Flavor rules enforced: potes cannot be added to cart without valid flavor count
- [ ] Schedule enforcement: ordering blocked outside hours, "Cerrado" shown
- [ ] Passthrough delivery accounting verified for `tercerizado` + `en_pedido`
- [ ] Multi-role employee tested: single user performs all 5 roles in sequence
- [ ] Zero critical/severe bugs open
- [ ] Documentation: API specs, deployment guide, merchant onboarding guide