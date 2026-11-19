# Tickets de pedidos: comandera configurable + consultas históricas

Objetivo: impresión de ticket al pasar a PREPARACION con cola y reimpresión, configurable por empresa; vista CONSULTAS (todo el personal) para ver/reimprimir tickets históricos.
Rama: feat/catalogs-per-company-pr1-foundation · Entrega: commits por unidad, push lo decide la usuaria · Runner: backend `..\.venv\Scripts\python.exe -m pytest apps -q` (venv del repo, NO el python global), frontend `npx vitest run` + `npm run build`.

## Specs

- S1 (usuario, verbatim): "cuando el pedido pasa preparacion, deberia imprimir un ticket en una comandera, deberia ser configurable dependiendo la empresa, por ej. en una heladeria si tiene que imprimir el ticket, pero en mas loca que una cabra no es necesario."
- S2 (usuario, verbatim): "cola de impresion, y reimprimir por si se trababa el papel."
- S3 (usuario, verbatim): "Arriba de empleados podemos poner CONSULTAS, y que se puedan ver los tickets, todo el personal deberia acceder, por si el error paso en su turno."
- S4 (contexto del reclamo, no cita): el reclamo referencia un pedido de ayer a las 15hs; CONSULTAS debe encontrar pedidos por fecha, código y cliente.
- Criterios: impresión = vista ticket 58mm por navegador (window.print), sin integración ESC/POS en esta etapa. La cola crea un PrintJob por pedido (único por pedido) al entrar a PREPARACION solo si la empresa tiene el flag. Marcar impreso queda registrado (printed_at); reimpresión disponible desde la cola pendiente y desde CONSULTAS. CONSULTAS visible para todo el personal en el menú (arriba de Empleados).

## Tasks

- T1 (S1,S2) backend: flag `Merchant.print_tickets` + migración; modelo `PrintJob` (order único, printed_at, printed_count) + migración; hook en OrderTransitionView al pasar a PREPARACION; endpoints GET /v1/print-jobs/ (pendientes) y POST /v1/print-jobs/{id}/printed/. Tests: job se crea solo con flag, único, marca impreso. → inline
- T2 (S3,S4) backend: filtros `code` y `customer` (nombre/teléfono icontains) en OrderBoardView. Tests. → inline
- T3 (S1,S2) frontend: componente TicketOrder (ticket 58mm); en kanban: badge de pendientes + dialog con tickets, Imprimir (window.print + marcar impreso), reimprimir pendiente. → inline
- T4 (S3,S4) frontend: vista CONSULTAS (rango de fechas default HOY por cambio L5, búsqueda por código/cliente, ticket con Reimprimir) + menú arriba de Empleados + ruta. → inline
- T5 (S1) config UI: MerchantSerializer agrega print_tickets; switch en edición de empresa (master) y en Django admin. → inline
- T6 (all) suites completas backend+frontend, build, commits por unidad. → inline

## Log

- L1 (2026-11-13, verbatim): "1- cuando el pedido pasa preparacion, deberia imprimir un ticket en una comandera, deberia ser configurable dependiendo la empresa, por ej. en una heladeria si tiene que imprimir el ticket, pero en mas loca que una cabra no es necesario. Y 2- supongamos que hacen un reclamo del pedido que se envio ayer a las 15 hrs, donde consulto los tickets?"
- L2 (2026-11-13, decisiones): "1 - cola de impresion, y reimprimir por si se trababa el papel. 2 - Arriba de empleados podemos poner CONSULTAS, y que se puedan ver los tickets, todo el personal deberia acceder, por si el error paso en su turno". Impresión por navegador elegida (sin ESC/POS por ahora); cola con job único por pedido; Consultas sin restricción de rol.
- L3 (2026-11-13, T1-T5 implementado, inline): backend flag print_tickets (tenancy 0008) + PrintJob (orders 0005) + hook en transición + GET /v1/print-jobs/ + POST /print-jobs/{id}/printed/ + filtros code/customer en board; frontend printing.api, utils/ticket.ts (builder compartido pantalla/papel), usePrinting, kanban badge+dialog, AdminConsultasView + menú + ruta, master edit switch, Django admin, MerchantSerializer. Commits bb7e8bf, 4fc5e87, 9bf686b, 21ba30f. Suites: 306 backend, 45 frontend, build OK. Pendiente: T6 cerrado con estas suites; usar activando el flag en una empresa con impresora real.
- L4 (2026-11-14, corrección de UX en CONSULTAS, inline): la búsqueda no filtraba en tiempo real y un teléfono (todo dígitos) se enviaba como `code` exacto, por lo que nunca encontraba el pedido; el alert "Sin pedidos para esos filtros" quedaba sin forma de volver. Fix: backend agrega parámetro `q` (OR sobre code__icontains, customer_name__icontains, customer_phone__icontains; se conservan `code`/`customer`); frontend manda `q`, re-aplica filtros con debounce 400ms sobre fechas y texto (Enter/botón siguen aplicando al instante), y limpiar el campo vuelve a la lista por defecto. Tests: q filter backend (RED→GREEN) + AdminConsultasView spec (tiempo real, debounce, volver al limpiar). Suites: 307 backend, 46 frontend, build OK.
- L5 (2026-11-14, verbatim): "si que habran con hoy por defecto, porque puede pasar que tambien reclamen de hoy" y "para que sea mas entendible, que sea consulta y por defecto la fecha del dia". Cambio: CONSULTAS abre con Desde/Hasta = hoy (isoDaysAgo(0) en refs, estado aplicado y fallback de fechas vacías); antes era ayer por L1/L2. Tests: spec "opens with today by default" RED→GREEN; suites 47 frontend, build OK (backend sin cambios).

