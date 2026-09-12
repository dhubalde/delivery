# Catalogs per Company & Client Registration — Spec + Slug API + Rollback

Purpose: Isolate storefronts per merchant via slug + per-merchant buyer identity. Covers Phase 4 verification and Phase 5 cleanup of the SDD change `catalogs-per-company-client-registration`.

## Slug API

All public storefront endpoints are isolated by `<slug>` (Merchant.slug) and are `AllowAny`. Inactive or unknown slugs return 404 via `_get_merchant_by_slug`.

| Method | Path | Auth | Success | Notes |
|--------|------|------|---------|-------|
| `GET` | `/api/public/<slug>/catalog` | none (AllowAny) | 200 `{merchant,categories,products,flavors,stats}` | Filtered by `merchant_id`; excludes inactive entities. Also supports trailing slash. |
| `GET` | `/api/public/<slug>/products` | none | 200 `[product]` | Query `?category=&search=` optional. |
| `GET` | `/api/public/<slug>/categories` | none | 200 `[category]` |  |
| `GET` | `/api/public/<slug>/flavors` | none | 200 `[flavor]` |  |
| `GET` | `/api/public/<slug>/stat` | none | 200 `{visit_count,buyer_count}` | `POST` increments visit. |
| `POST` | `/api/public/<slug>/customers/register` | none | 201 `{customer,tokens,access,refresh}` | Body `phone,name,password>=6`; 409 if `(merchant,phone)` exists. Gate `CUSTOMER_AUTH_ENABLED`. |
| `POST` | `/api/public/<slug>/customers/login` | none | 200 `{customer,tokens,access,refresh}` | 401 no leak. |
| `GET` | `/api/public/<slug>/customers/me` | `Authorization: Customer <jwt>` | 200 `{id,phone,name,merchant_slug,merchant_id}` | 401 if missing/invalid, 403 if `mid != slug`. Distinct prefix from `Bearer`. |
| `POST` | `/api/public/<slug>/orders` | none or `Customer <jwt>` | 201 `{id,code,total}` | Header `Idempotency-Key` required. Guest if missing/mismatched `mid`; link `Order.customer` only when `mid==slug`. |

Routing guarantee: `config/urls.py` defines `api/public/<slug>/` exactly once for `apps.orders.urls_public` and once for `apps.customers.urls_public`; `apps.catalog.urls_public` is included via `api/public/` with inner `<slug:slug>/...`. No bare `api/public/orders` route exists — `POST /api/public/orders` → 404. `apps.orders.urls_public` must not contain `path("",...)` legacy root.

JWT contract (customer): SimpleJWT access/refresh with claims `mid` (merchant id) and `cid` (customer id). Header `Customer <token>` — never `Bearer`. Middleware does not parse `Customer`, so `CustomerJWTAuthentication` is authoritative. Mismatched token on orders never fails — falls back to guest.

Frontend slug routing: SPA mounted at `/:slug` with children `/:slug/checkout` and `/:slug/my-orders`. `/:pathMatch(.*)*` → `NotFoundView`. Root `/` redirects to `/ice-zone`. State partitioned by `localStorage` keys `cart:{slug}`, `myOrders:{slug}`, `customer:{slug}`. `CatalogView` fetches `/api/public/{slug}/catalog` via `route.params.slug`; 404 → NotFound. `api/client.ts` interceptor attaches `Customer` header only for `.../orders` and `.../customers/me` when a token for that slug exists, and strips `Bearer` on public calls.

## Verification (Phase 4)

- Unit: `Customer` `UniqueConstraint(merchant,phone)`, cross-merchant phone allowed, password hash, JWT `mid/cid`, `mid` mismatch → 403.
- Integration: catalog isolation (acme excludes beta), inactive slug → 404, guest/auth/mismatched order linking, duplicate URL 404 vs 201, `Bearer` on `customers/me` → 401.
- Frontend Vitest: `npm run test` covers `router /:slug`, `cartKey`/`customerKey`/`myOrdersKey` two-slug isolation, `api/client` slug extraction and header attachment.
- Smoke (single flow): `/acme/catalog` 200 isolated, `/acme/orders` guest 201, `POST /acme/customers/register` 201 → `POST /acme/orders` with `Customer` → linked `Order.customer`, `/beta/catalog` excludes acme data plus `POST /beta/orders` with acme token → guest (no cross-link), `POST /api/public/orders` 404.

Commands:

```bash
# backend
python -m pytest apps/customers/tests/ apps/catalog/tests/test_public_catalog_aggregate.py apps/orders/tests/test_public_order_customer_link.py apps/orders/tests/test_public_orders_isolation.py apps/orders/tests/test_order_customer_fk.py apps/catalog/tests/test_smoke_catalog_isolation.py -v
# or: pytest
# frontend
npm run test --prefix frontend
```

## Feature Gate (Phase 5.1)

Environment variable `CUSTOMER_AUTH_ENABLED` (default `"1"`).

- `1`: customer endpoints (`api/public/<slug>/customers/*`) are mounted and register/login/me are active; orders parse `Customer` JWT opportunistically.
- `0`: customers include is not added in `config/urls.py`; all `customers/*` requests are 404; `CustomerRegisterView/LoginView/MeView` raise 404 via `_check_customer_auth_gate()` even if routed; `POST /api/public/<slug>/orders` still succeeds as guest and ignores `Customer` header (no link). Allows instant rollback without migrations.

Legacy cleanup: `config/urls.py` now contains exactly one `include("apps.orders.urls_public")` under `api/public/<slug>/` and zero bare `api/public/` duplicate for orders; `apps/orders/urls_public.py` no longer defines `path("", ...)` or `name="public-order-create-root"`.

## Rollback Plan (Phase 5.2)

Order matters — FK before table because `orders_order.customer_id` references `customers_customer`.

```bash
# 1. Gate off customer endpoints (no code rollback needed)
CUSTOMER_AUTH_ENABLED=0 python manage.py runserver

# 2. If full DB revert is needed, reverse migrations in order:
python manage.py migrate orders 0002_add_cancel_reason
# removes FK orders_order.customer_id (0003 reverse)
python manage.py migrate customers zero
# drops customers_customer table + UniqueConstraint/Index (0001 reverse)

# 3. Code revert (if gate not enough):
git revert <PR3> <PR2> <PR1>  # keeps guest checkout; cart/myOrders partition falls back to legacy keys if needed
# or keep frontend but tolerate missing customer endpoints — guest flow unchanged
```

Guest checkout is unaffected by rollback; no backfill of `Order.customer` is required. Until verified, frontend keeps `merchantSlug` fallback removed only after smoke passes; `customer` store already tolerates missing keys.

## Success Criteria

- [x] `GET /public/<slug>/catalog` isolated per merchant
- [x] `/:slugA` never shows `slugB` cart/myOrders/customer
- [x] Guest `POST /public/<slug>/orders` works (AllowAny, no Bearer required)
- [x] Register/login → customer JWT links order when `mid==slug`, else guest
- [x] No duplicate `api/public` include; bare `/public/orders` → 404

Open spec deltas: `merchant-catalog`, `customer-identity`, `tenant-isolation` (see `openspec/changes/catalogs-per-company-client-registration/specs/`).
