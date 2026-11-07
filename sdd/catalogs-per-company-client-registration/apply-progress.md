# Apply Progress: Catalogs per Company & Client Registration

**Change**: catalogs-per-company-client-registration
**Mode**: Standard (strict_tdd false)
**Branch**: feat/catalogs-per-company-pr1-foundation (stacked-to-main, from feat/delivery-panel-pr6-weather-errors) — PR3 Frontend stacked
**Date**: 2026-09-12

## Completed Tasks

### Phase 1: Foundation (PR1)
- [x] 1.1 Fix `backend/config/urls.py` — single `api/public/<slug:slug>/` include; remove duplicate bare/double slug
- [x] 1.2 Create `backend/apps/customers/models.py` — `Customer(merchant FK, phone, name, password_hash)` + `UniqueConstraint(merchant,phone)` + `customers` in INSTALLED_APPS + migration 0001
- [x] 1.3 Add `customer FK (SET_NULL, nullable)` to `backend/apps/orders/models.py` + migration 0003 (depends on customers 0001)
- [x] 1.4 RED — duplicate shadows slug: `POST /public/orders→404` vs `POST /public/acme/orders→201`

### Phase 2: Backend (PR2)
- [x] 2.1 Add `PublicCatalogAggregateView` in `backend/apps/catalog/views_public.py` + `<slug>/catalog` in `backend/apps/catalog/urls_public.py` — `AllowAny` via `_get_merchant_by_slug`→404 (aggregate categories+products+flavors+stats, merchant isolated, inactive→404)
- [x] 2.2 Create `backend/apps/customers/auth.py` + `views.py` (register/login/me) + `urls_public.py` `<slug>/customers/*`; SimpleJWT `mid/cid`, header `Customer` distinct from Bearer, 409/401/403 handling
- [x] 2.3 Modify `backend/apps/orders/views.py` — parse `Customer` JWT; `mid==slug`→link else guest (no fail), Bearer ignored, invalid/mismatched fallback to guest
- [x] 2.4 RED — AllowAny: `GET /public/acme/catalog` no auth→200; `POST /public/acme/orders` guest→201 (threat: Bearer)
- [x] 2.5 RED — prefix: `Bearer` on `customers/me`→401 vs `Customer`→200 (threat: prefix collision)
- [x] 2.6 RED — inactive: `GET /public/inactive/catalog`→404, `POST /public/inactive/customers/register`→404, `POST /public/inactive/orders`→404 (threat: inactive leak)
- [x] 2.7 RED — cross-merchant: `GET /public/acme/catalog` excludes beta entities, `GET /public/beta/customers/me` with acme JWT→403, mismatched order token→guest no cross-link (threat: slug leak)

### Phase 3: Frontend (PR3)
- [x] 3.1 Modify `frontend/src/router/index.ts` — `/:slug` with `checkout`/`my-orders`; invalid→`NotFoundView`. Root `/` redirects to `/ice-zone` (default slug) preserving chooser fallback.
- [x] 3.2 Create `frontend/src/stores/customer.store.ts` — keys `customer:{slug}`, `register/login/me/logout` with SimpleJWT `mid/cid` via `Customer` header isolation per slug. Branding via `PublicLayout` `useCatalog` merchant name.
- [x] 3.3 Modify `frontend/src/stores/cart.store.ts` (`cart:{slug}`) + `frontend/src/composables/useMyOrders.ts` (`myOrders:{slug}`) + `frontend/src/api/client.ts` attach `Customer` header opportunistic per slug (guest fallback, no Bearer leak on public).
- [x] 3.4 Modify `frontend/src/views/CatalogView.vue` — `slug=route.params.slug`, fetch `GET /api/public/{slug}/catalog` via `useCatalog`, 404→`NotFoundView`, client-side category/search filter on aggregate, hydrates `cart`/`customer` stores per slug.

## Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `backend/config/urls.py` | Modified (PR1/PR2) | Kept `api/public/` (catalog) + `api/public/<slug:slug>/` (orders); added `api/public/<slug:slug>/` include for `apps.customers.urls_public` (customers/register, login, me) |
| `backend/apps/catalog/views_public.py` | Modified (PR2) | Fixed `_get_merchant_by_slug` to check `deleted_at`+`is_active`→404; added `PublicCatalogAggregateView` (AllowAny, authentication_classes=[], returns merchant+categories+products+flavors+stats scoped by merchant_id) |
| `backend/apps/catalog/urls_public.py` | Modified (PR2) | Added `<slug:slug>/catalog` and `<slug:slug>/catalog/` routes for aggregate |
| `backend/apps/customers/auth.py` | Created (PR2) | `get_tokens_for_customer(customer)` → Refresh+Access with claims `mid`/`cid`; `CustomerJWTAuthentication` parsing `Customer <jwt>` distinct from Bearer, validates mid/cid, loads Customer |
| `backend/apps/customers/views.py` | Created (PR2) | `CustomerRegisterView`/`CustomerLoginView` (AllowAny, 201/200 with JWT, 409 duplicate, 401 invalid), `CustomerMeView` (requires `Customer` header, 401 missing/invalid, 403 cross-merchant, 200 profile); helper `_get_merchant_by_slug_or_404` enforces active/inactive 404 |
| `backend/apps/customers/urls_public.py` | Created (PR2) | `customers/register`, `customers/login`, `customers/me` (+ slash variants) — mounted at `api/public/<slug:slug>/` → final `/api/public/<slug>/customers/*` |
| `backend/apps/orders/views.py` | Modified (PR2) | Added `_get_customer_for_order` (parses `Customer <jwt>` via `AccessToken`, verifies mid==merchant.pk else None, invalid→None), `_get_merchant_by_slug_or_404` (active check), updated `PublicOrderCreateView.post` to resolve merchant via new helper, opportunistic link `Order(customer=customer)` if valid else guest; mismatched/Bearer/invalid never blocks |
| `frontend/src/router/index.ts` | Modified (PR3) | Replaced root `/` PublicLayout with redirect to `/ice-zone`; added `/:slug` parent with children `''` (catalog), `checkout`, `my-orders`; static routes (`/panel`, `/master`, `/login`, `/change-password`) ordered before dynamic `/:slug`; catch-all NotFound last. Root `/{slug}` unknown now still resolves but CatalogView shows NotFound on 404. |
| `frontend/src/stores/customer.store.ts` | Created (PR3) | Pinia store `customer` with per-slug localStorage `customer:{slug}` (access/refresh/profile), actions `hydrate/setSlug/persist/register/login/fetchMe/logout/getAccessForSlug`, isolates JWT per merchant, uses `api.post /public/{slug}/customers/*` with `Customer` header separate from `Bearer`. |
| `frontend/src/stores/cart.store.ts` | Modified (PR3) | Partitioned by `cart:{slug}`: added `cartKey(slug)`, `readCart/writeCart`, state `_slug/_hydratedSlug`, actions `hydrate/setSlug/persist` with per-change persistence; `add/remove/inc/dec/clear` now persist per slug. Initial `cart.clear()` respects slug param. |
| `frontend/src/composables/useMyOrders.ts` | Modified (PR3) | Partitioned by `myOrders:{slug}`: added `myOrdersKey`, `getMyOrderIdsForSlug/addMyOrderIdForSlug/removeMyOrderIdForSlug`, slug inference from `window.location.pathname`, `useMyOrders(slug?)` with `['myOrders', slug, ids]` queryKey, storage listeners per slug. Legacy `myOrders` key kept as fallback. |
| `frontend/src/composables/useCatalog.ts` | Created (PR3) | `useCatalog(slug)` → `GET /public/{slug}/catalog` via vue-query, `AllowAny`, `retry:false`, `qk` `['catalog','aggregate',slug]`, returns merchant/categories/products/flavors/stats aggregate. |
| `frontend/src/api/client.ts` | Modified (PR3) | Added `extractPublicSlug` and `getCustomerAccessForSlug`; request interceptor now skips `Bearer` for `/public/` endpoints, attaches `Authorization: Customer <jwt>` only for `/public/{slug}/orders` and `/public/{slug}/customers/*` when token exists for that slug; guest public requests explicitly delete leaked Bearer. Keeps `Idempotency-Key` and `/v1/` X-Merchant-Slug handling for admin. |
| `frontend/src/views/CatalogView.vue` | Modified (PR3) | Now `slug=route.params.slug`, `watch slug` hydrates `cart`/`customer` stores, `useCatalog(slug)` fetches aggregate, `isNotFound` renders `NotFoundView` on 404, client-side category/search filtering on aggregate products. Removed `auth.merchantSlug` dependency. |
| `frontend/src/layouts/PublicLayout.vue` | Modified (PR3) | Hydrates `cart`/`customer` per `route.params.slug`, shows merchant name from `useCatalog(slug).data.merchant.name`, slot header customer `displayName` + logout button `customer.logout(slug)`, passes `slug` to `CartDrawer`, retains theme/offline handling. |
| `frontend/src/components/CartDrawer.vue` | Modified (PR3) | Now slug-aware: prop `slug?`, computed `routeSlug` from prop or `window.location`, `watch` hydrates `cart`, `useMenu(routeSlug)` for open/closed, `checkoutTo = /{slug}/checkout`, button `:to="checkoutTo"`. Removed `auth` dependency. |
| `frontend/src/views/CheckoutView.vue` | Modified (PR3) | Uses `route.params.slug`, hydrates `cart`/`customer`, `useMenu(slug)`, `addMyOrderIdForSlug(id, slug)` partitioning, posts to `/public/{slug}/orders` (api client attaches Customer header), redirects to `/{slug}` after success. |
| `frontend/src/views/MyOrdersView.vue` | Created (PR3) | Wrapper view for `/:slug/my-orders` route displaying `MyOrders` component with back button to `/{slug}` catalog. |

## Work Unit Evidence (PR1)

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `python -m pytest apps/customers/tests/test_models.py apps/orders/tests/test_public_orders_isolation.py apps/orders/tests/test_order_customer_fk.py -v` — 18 passed in 14.52s |
| Runtime harness command/scenario and exact result | `POST /api/public/orders` without slug → 404; `POST /api/public/acme/orders` with valid product and open Schedule → 201 |
| Rollback boundary | Revert `backend/config/urls.py` + `apps/orders/urls_public.py` + drop FK via `migrate orders 0002` then `migrate customers zero` |

## Work Unit Evidence (PR2)

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `python -m pytest backend/apps/catalog/tests/test_public_catalog_aggregate.py backend/apps/customers/tests/test_customer_auth.py backend/apps/orders/tests/test_public_order_customer_link.py backend/apps/customers/tests/test_models.py backend/apps/orders/tests/test_public_orders_isolation.py backend/apps/orders/tests/test_order_customer_fk.py -v` — 49 passed in 24.69s (31 new PR2 + 18 PR1). Subset PR2-only: `python -m pytest backend/apps/catalog/tests/test_public_catalog_aggregate.py backend/apps/customers/tests/test_customer_auth.py backend/apps/orders/tests/test_public_order_customer_link.py -v` — 31 passed (7 catalog aggregate + 16 customer auth + 8 order link) |
| Runtime harness command/scenario and exact result | `GET /api/public/acme/catalog` no auth → 200 with isolated merchant/categories/products/flavors/stats; `GET /api/public/ghost/catalog` → 404; `GET /api/public/inactive/catalog` → 404; `POST /api/public/acme/customers/register` → 201 with access containing mid/cid; `POST /api/public/acme/customers/login` correct→200 vs wrong→401; `GET /api/public/acme/customers/me` `Customer <jwt>`→200 vs `Bearer <same>`→401 vs cross-merchant→403; `POST /api/public/acme/orders` guest no header→201 customer None, with valid Customer header→201 linked, with beta token→201 guest (no block) — all verified via APIClient in tests |
| Rollback boundary | Revert `backend/apps/catalog/views_public.py` (remove PublicCatalogAggregateView, restore old _get_merchant_by_slug), `backend/apps/catalog/urls_public.py` (remove catalog routes), `backend/apps/customers/auth.py`, `backend/apps/customers/views.py`, `backend/apps/customers/urls_public.py`, `backend/config/urls.py` (remove customers include), `backend/apps/orders/views.py` (remove _get_customer_for_order/_get_merchant_by_slug_or_404 and customer=kwarg in Order.create). No migration to revert (PR2 adds no schema). Tests `test_public_catalog_aggregate.py`, `test_customer_auth.py`, `test_public_order_customer_link.py` can be deleted together. |

## Work Unit Evidence (PR3)

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `npm run typecheck` — `vue-tsc --noEmit` passed (0 errors); `npm run build` — `vite build` succeeded in 5.17s (vendor 204k, vuetify 61k, CatalogView 6.55k, PublicLayout 7.96k, CheckoutView 8.74k, customer.store 4.09k, useMyOrders 2.98k, MyOrdersView 0.92k). No Vitest suite yet (`npm run test -- stores router` — no tests found; build/typecheck is harness for this slice). |
| Runtime harness command/scenario and exact result | Manual slug partition check (localStorage): `cart:acme` vs `cart:beta` isolated — `useCartStore('acme').add()` does not appear in `useCartStore('beta').items`; `myOrders:acme=[1,2]` vs `myOrders:beta=[]` via `getMyOrderIdsForSlug`/`addMyOrderIdForSlug`; `customer:acme` JWT not attached when POST ` /public/beta/orders` (interceptor `extractPublicSlug` mismatch → guest); `GET /public/acme/catalog` → 200 aggregate; `GET /public/ghost/catalog` → CatalogView renders NotFoundView (error 404). `/:slug/checkout` and `/:slug/my-orders` resolve under `/:slug` parent; `/` redirects to `/ice-zone`; `/panel`/`/master`/`/login` still matched before `/:slug` (order verified). |
| Rollback boundary | Revert `frontend/src/router/index.ts` (restore root PublicLayout at `/`), delete `frontend/src/stores/customer.store.ts` + `frontend/src/composables/useCatalog.ts` + `frontend/src/views/MyOrdersView.vue`, revert `frontend/src/stores/cart.store.ts` (remove cart:{slug} partition), revert `frontend/src/composables/useMyOrders.ts` (restore single MY_ORDERS_KEY), revert `frontend/src/api/client.ts` (remove Customer header + publicSlug logic), revert `frontend/src/views/CatalogView.vue` (restore auth.merchantSlug + useProducts), revert `frontend/src/layouts/PublicLayout.vue` (restore auth-based header) + `frontend/src/components/CartDrawer.vue` + `frontend/src/views/CheckoutView.vue` (restore auth merchantSlug). No backend changes. |

## Deviations from Design

None — follows `design.md` scoped Customer JWT `mid`+`cid` via SimpleJWT, distinct `Customer` prefix (middleware only parses `Bearer`), catalog aggregate single AllowAny call filtered by merchant_id via `_get_merchant_by_slug`→404 for inactive/unknown, order opportunistic linking (mid==slug else guest, never fails). Config keeps `api/public/` for catalog and `api/public/<slug:slug>/` for orders+customers (both resolve to `/api/public/<slug>/*`, catalog via inner slug, orders/customers via outer slug — consistent per tasks). Frontend PR3 stores partition per `cart:{slug}`, `myOrders:{slug}`, `customer:{slug}`; `api/client` attaches `Customer` only for orders/me per slug, guest fallback never fails, router `/:slug` parent with `checkout`/`my-orders`, root `/` redirect fallback, invalid slug renders NotFound via catalog 404.

## Issues Found

- `_get_merchant_by_slug` previously returned inactive/soft-deleted merchants (found via `all_objects` fallback then `get_object_or_404` on live manager) — fixed to check `deleted_at` and `is_active` explicitly and raise Http404, now all public endpoints correctly 404 for inactive.
- `PublicOrderCreateView` previously used `get_object_or_404(Merchant, slug=slug)` which also returned inactive — replaced with active-check helper.
- SimpleJWT `RefreshToken()` without user generates valid tokens with mid/cid but no `user_id` — `AccessToken` validation only checks signature/exp, so `CustomerJWTAuthentication` validates correctly; no session table needed.
- Frontend `api/client` previously attached `Bearer` to public endpoints, leaking Work Zone JWT to AllowAny — fixed to skip Bearer for `/public/` and only attach `Customer` per slug for orders/me, ensuring threat “public endpoint requires Bearer” (AllowAny) and prefix isolation remain valid.
- `useMyOrders` and `cart` previously single-key storage — partition required slug inference from `window.location` fallback plus explicit `ForSlug` helpers for testability; legacy `myOrders` key retained as fallback to avoid data loss on upgrade.

## Remaining Tasks

- [ ] 4.1–4.4 Verification + smoke (unit/integration/frontend Vitest + smoke acme/beta/ghost/mismatched)
- [ ] 5.1–5.2 Cleanup + docs (remove legacy orders `""` path if present, gate `CUSTOMER_AUTH_ENABLED`, document slug API)

## Workload / PR Boundary

- Mode: stacked PR slice (PR3 Frontend) — `stacked-to-main`
- Current work unit: 3 `/:slug` routing + partitioned stores + header (Phase 3, tasks 3.1–3.4)
- Boundary: Starts after PR2 (catalog aggregate + customer auth + order link). Ends after frontend slug routing (`/:slug`, `/checkout`, `/my-orders`), per-slug storage (`cart:{slug}`, `myOrders:{slug}`, `customer:{slug}`), Customer header attachment, and CatalogView aggregate fetch with NotFound handling. Does not include Phase 4 verification (4.1–4.4) or Phase 5 cleanup (5.1–5.2).
- Estimated review budget impact: ~180 prod lines (router + customer.store + useCatalog + client + CatalogView + PublicLayout/CartDrawer/Checkout) + small store helpers; total PR3 prod diff ≈220 lines, within 400 budget. Chain strategy `stacked-to-main`.

## Status

15/21 tasks complete (Phase 1 + Phase 2 + Phase 3). Ready for verify (Phase 4).
