# Pagos en línea: Mercado Pago (billeteras + tarjetas) y links de pago

Objetivo: cobros online con Mercado Pago. En el checkout el cliente elige efectivo (cobra el moto al entregar) o pagar en línea (billetera/tarjeta) y el pedido entra al kanban recién cuando MP confirma el pago. Para ingresos manuales, el staff genera un link de pago para transferencia; al confirmarse, el pedido queda pagado.
Rama: feat/catalogs-per-company-pr1-foundation · Entrega: commits por unidad, push lo decide la usuaria · Runner: backend `python -m pytest apps -q` (GLOBAL python), frontend `npx vitest run` + `npm run build`.
Integración: Mercado Pago Checkout Pro (redirect). Los datos de tarjeta nunca pasan por nuestro servidor. Credenciales por empresa (access_token en config), sandbox primero. Dependencia externa: la usuaria crea la app en el panel de MP y carga las credenciales; el código se testea con HTTP mockeado (sandbox requiere red).

## Specs

- S1 (usuario, verbatim): "Si compras por catalogo, podes elegir efectivo( cobra moto cuando entrega), billeteras o tarjetas de creditos o debito, cuando ingresa el pedido queda pagado!"
- S2 (usuario, verbatim): "despues tenes el ingreso manual, para personas que no manejan la web, que puede ser en efectivo o transferencia ( que se le envia el link al cliente), cuando llega la transferencia ingresa el pedido."
- S3 (usuario, verbatim): "la primera" — el pedido entra al kanban recién cuando MP confirma el pago (no entra bloqueado).
- S4 (evaluación aceptada, no cita): NO se imprime ticket al confirmar el pago; el ticket se sigue imprimiendo al pasar a PREPARACION con el flag print_tickets (un único disparador).
- S5 (decisión de arquitectura): un solo motor — preferencia de MP atada al pedido + webhook de confirmación; checkout online y link manual son dos puertas de la misma pieza.

## Tasks

- [x] T1 (S1) backend: config MP por empresa — `Merchant.mp_access_token`, `mp_webhook_secret` (migración 0009); write-only en master PATCH + flag público `has_online_payments`; Django admin. Tests (`test_merchant_payment_config.py`). Commit `f01e6e2`.
- [x] T2 (S5) backend: adapter `apps/payments/gateways/mercado_pago.py` — create_preference → {id, init_point}; get_payment normalizado {status, method, amount, external_reference}; validate_signature (manifest `id/request-id/ts`). HTTP mockeable. Tests (`test_gateway.py`). Commit `fe5b0a4`.
- [x] T3 (S5) backend: endpoints — POST /public/{slug}/orders/{id}/pay y POST /v1/orders/{id}/payment-link/ (staff); idempotentes (reusan preferencia). Tests RED→GREEN (`test_online_payments.py`). Commit `e2c961f`.
- [x] T4 (S2,S3) backend: webhook público POST /api/payments/webhook/{merchant-slug}/ — valida firma si hay secreto, re-consulta pago en MP (`PaymentService.fetch_gateway_payment`), confirma Payment (method desde MP) idempotente. Tests RED→GREEN. Commit `e2c961f`.
- [x] T5 (S3) backend: guard en transición (`PaymentService.validate_online_paid` en PREPARACION/LOGISTICA → 409); board excluye pedidos con Payment ONLINE PENDING (Exists). Tests. Commit `e2c961f`.
- [x] T6 (S1) frontend checkout: modo efectivo vs en línea (si `has_online_payments`); en línea → crea pedido (ONLINE PENDING) → POST pay → `redirectTo(init_point)`. Tests `CheckoutView.spec.ts` (web cash/online). Commit `3b8cad2`.
- [x] T7 (S2) frontend staff (parcial): ingreso manual con método ONLINE genera link y muestra diálogo copiar/WhatsApp; al cerrar vuelve al tablero y sale de modo operador. Test `CheckoutView.spec.ts`. Commit `5253263`. Nota: no se agregó chip de estado de pago en el board (pedidos online pendientes quedan ocultos hasta confirmación por S3).
- [x] T8 (S1) frontend config: campos Access token / Webhook secret en edición de empresa (master) — se envían solo si se completan (no pisan valores existentes). Tipos API actualizados. Build OK. Commit `913d8d0`. Sin test de componente dedicado (sin spec previo de la vista).
- [x] T9 (all) suites completas backend+frontend, build, commits por unidad. Backend `python -m pytest apps -q`: 324 passed. Frontend `npx vitest run`: 50 passed. `npm run build`: OK. Dependencia externa pendiente: credenciales MP reales + validación en sandbox por la usuaria.

## Log

- L1 (2026-11-16, verbatim): "si seguimos con la parte de pagos, que deberiamos conectar a las diferentes billeteras, tarjetas de creditos, y no se como hacerlo"
- L2 (2026-11-16, decisiones del usuario, verbatim): "Si compras por catalogo, podes elegir efectivo( cobra moto cuando entrega), billeteras o tarjetas de creditos o debito, cuando ingresa el pedido queda pagado!, despues tenes el ingreso manual, para personas que no manejan la web, que puede ser en efectivo o transferencia ( que se le envia el link al cliente), cuando llega la transferencia ingresa el pedido."
- L3 (2026-11-16, verbatim): "la primera" — pedido entra al kanban solo al confirmarse el pago.
- L4 (2026-11-16, evaluación): no se imprime ticket al confirmar pago; disparador único en PREPARACION (S4).
- L5 (2026-11-16): espejo Engram pendiente — `mem_current_project` no disponible en este runtime, proyecto no resoluble; el documento vive en `odd/tasks/online-payments.md`.
- L6 (2026-11-18): backend T1-T5 implementado (test-first, HTTP mockeado). Commits: `f01e6e2` (credenciales Merchant + migración tenancy 0009), `fe5b0a4` (adapter MP Checkout Pro), `e2c961f` (pay endpoints público/staff, webhook `/api/payments/webhook/<slug>/` con firma+fetch, Payment.ONLINE/checkout_url migración payments 0004, board exclusion, guard de transición). Suite apps/orders+apps/payments 105 passed en ese punto.
- L7 (2026-11-18): frontend T6-T8 implementado. Checkout web con toggle efectivo/en línea (`has_online_payments`), redirect a `init_point`; flujo manual con método ONLINE genera link y diálogo copiar/WhatsApp; campos MP en edición master de empresa. Commits: `3b8cad2`, `5253263`, `913d8d0`. Fix aplicado: `sumError` no bloquea checkout web (el monto se fija en submit; el ref inicial podía anteceder la hidratación del carrito). Polyfills jsdom (`ResizeObserver`/`visualViewport`) en `src/test/setup.ts` para specs con Vuetify.
- L8 (2026-11-18): verificación final — backend `python -m pytest apps -q` 324 passed; frontend `npx vitest run` 50 passed; `npm run build` OK. Espejo Engram sigue pendiente (proyecto no resoluble en este runtime). Pendiente externo: cargar credenciales reales de la app Mercado Pago y validar flujo completo en sandbox con la usuaria. Push no realizado.
