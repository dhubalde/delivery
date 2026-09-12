# Design: Catalogs per Company & Client Registration

## Technical Approach
Scoped tenancy: isolate storefront per `Merchant.slug` + per-merchant `Customer` JWT. Backend adds `apps/customers`, `PublicCatalogAggregateView` (`GET /public/<slug>/catalog`), `Order.customer` FK. Frontend moves SPA to `/:slug/*` and partitions `cart`/`myOrders`/`customer` by slug. `config/urls.py` deduplicates includes. Public endpoints `AllowAny` via `_get_merchant_by_slug` (404 if inactive).

## Architecture Decisions

### Decision: Customer isolation

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Global Customer (phone unique globally) | Leaks identity across tenants | Rejected |
| Global + MerchantCustomer join | Over-engineered, ACL complexity | Rejected |
| **Scoped `Customer(merchant FK, UniqueConstraint(phone,merchant))`** | Matches existing per-merchant patterns; defers SSO | **Chosen** |

**Rationale**: Follows `Employee`/`Category` patterns; `BaseModel` + `make_password`; no `auth.User`.

### Decision: Customer JWT

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Reuse `WorkZoneTokenView` / `Bearer` | Mixes buyer/admin privilege | Rejected |
| **New SimpleJWT `mid`+`cid`, `Authorization: Customer <jwt>`** | Isolated; middleware only parses `Bearer` | **Chosen** |

**Rationale**: `get_token` adds `mid`/`cid`; mismatch → 401/403.

### Decision: Catalog aggregate

| Option | Tradeoff | Decision |
|--------|----------|----------|
| 3 separate requests | Extra round-trips | Rejected |
| **Single `PublicCatalogAggregateView`** | One `AllowAny` call | **Chosen** |

**Rationale**: Filtered by `merchant_id`; reuses serializers.

### Decision: Slug routing & storage

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `?slug=` + single key | Cart bleeds | Rejected |
| **`/:slug` + keys `cart:{slug}`, `myOrders:{slug}`, `customer:{slug}`** | `route.params.slug` driven | **Chosen** |

**Rationale**: Shareable URLs; removes `auth.merchantSlug` dependency.

## Data Flow

```
FE /:slug → GET /public/{slug}/catalog → PublicCatalogAggregateView → _get_merchant_by_slug → filtered querysets → 200/404

FE POST /public/{slug}/customers/register|login → CustomerTokenView → hash/check → JWT{mid,cid} → customer.store[{slug}]
FE GET /public/{slug}/customers/me (Customer <jwt>) → verify mid==slug → 200/401|403

FE POST /public/{slug}/orders [guest or Customer <jwt>] → PublicOrderCreateView → if valid Customer jwt & mid==slug then Order.customer=cid else guest (never fails) → idempotency → 201
```

Guest always succeeds; mismatched `mid` falls back to guest, no cross-merchant link.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/apps/customers/models.py` | Create | `Customer` merchant FK, phone, password_hash; constraint+indexes |
| `backend/apps/customers/auth.py` | Create | `CustomerTokenSerializer` + `CustomerJWTAuthentication` |
| `backend/apps/customers/views.py` | Create | Register/login/me scoped by slug |
| `backend/apps/customers/urls_public.py` | Create | `<slug>/customers/*` |
| `backend/apps/catalog/views_public.py` | Modify | Add `PublicCatalogAggregateView` |
| `backend/apps/catalog/urls_public.py` | Modify | Add `<slug>/catalog` |
| `backend/apps/orders/models.py` | Modify | Add `customer FK (null, SET_NULL)` |
| `backend/apps/orders/views.py` | Modify | Parse Customer JWT, opportunistic link |
| `backend/config/urls.py` | Modify | Single slug-prefixed orders include |
| `frontend/src/router/index.ts` | Modify | `/:slug` parent |
| `frontend/src/stores/customer.store.ts` | Create | Per-slug JWT store |
| `frontend/src/stores/cart.store.ts` | Modify | `cart:{slug}` partition |
| `frontend/src/composables/useMyOrders.ts` | Modify | `myOrders:{slug}` partition |
| `frontend/src/views/CatalogView.vue` | Modify | `route.params.slug` |
| `frontend/src/api/client.ts` | Modify | Attach `Customer` header |

## Interfaces / Contracts

- **Customer**: `merchant FK CASCADE`, `phone Char(40)`, `name Char(120)`, `password_hash Char(128)`, `UniqueConstraint(merchant,phone)`.
- **JWT**: SimpleJWT access/refresh, claims `mid:int`, `cid:int`, header `Authorization: Customer <token>`.
- **Endpoints** (`AllowAny`; `me` requires Customer JWT):
  - `GET /public/<slug>/catalog` → 200 aggregate | 404
  - `POST /public/<slug>/customers/register` → 201+JWT | 409 / `POST /login` → 200+JWT | 401 / `GET /me` → 200 | 403
  - `POST /public/<slug>/orders` → 201 (guest or linked if mid matches)

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | UniqueConstraint cross-merchant, password, JWT claims, mid mismatch reject | Django TestCase |
| Integration | Catalog isolation, guest/auth order linking, mismatched token fallback, duplicate URL 404 | APITestCase |
| Frontend | Router `/:slug`, cart/myOrders/customer partition, NotFound on invalid slug | Vitest |

## Threat Matrix

`references/threat-matrix.md` not present — evaluated for routing/auth isolation:

| Threat | Applicable | Handling |
|--------|------------|----------|
| Cross-merchant leak via slug | Applicable | All views filter by `merchant_id` from `_get_merchant_by_slug` |
| Public endpoint requires Bearer | Applicable | `AllowAny` + `authentication_classes=[]` |
| JWT prefix collision | Applicable | `Customer` vs `Bearer` separate parsers |
| Duplicate include shadows slug | Applicable | Single slug-prefixed include; bare `/public/orders` → 404 |
| Slug injection | N/A | `<slug:slug>` converter, no shell/fs |
| Shell/VCS automation | N/A | No shell in change |
| Inactive merchant leak | Applicable | `_get_merchant_by_slug` → 404 if inactive |

## Migration / Rollout

Add `customers_customer` + nullable `orders_order.customer_id` (migration). Rollback: drop FK then table. No backfill; guest unaffected. Gate `CUSTOMER_AUTH_ENABLED` if needed.

## Open Questions

- [ ] Phone vs email unique key — phone chosen per spec?
- [ ] OTP on register — deferred?
- [ ] `/` → default slug / chooser / 404?
- [ ] Admin customer list — defer to phase 2?
