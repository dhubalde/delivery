# Proposal: Catalogs per Company & Client Registration

## Intent
Isolate storefronts per merchant via slug + add per-company buyer identity: slug catalog, partitioned cart/orders, merchant-scoped customer (separate JWT), guest checkout stays.

## Scope

### In Scope
- `GET /public/<slug>/catalog` aggregate
- Fix duplicate `api/public/<slug>/orders` include
- SPA `/:slug`, `/:slug/checkout`, `/:slug/my-orders`
- Partition `cart`/`myOrders` by slug
- `Customer(merchant FK, unique(phone,merchant))` + `Order.customer` FK
- `POST /public/<slug>/customers/register|login|me`

### Out of Scope
- Global SSO / cross-merchant customer
- Loyalty, coupons, billing per customer
- Theming / admin customer CRUD (phase 2)
- Migrating anonymous orders

## Capabilities

### New Capabilities
- `merchant-catalog`: slug-isolated catalog + aggregate + routing
- `customer-identity`: per-merchant customer auth (scoped JWT)

### Modified Capabilities
- `tenant-isolation`: public slug scope (AllowAny), fix duplicate

## Approach
**Option A — Scoped Customer (recommended).**
1. Backend `Customer(merchant FK)` + `CustomerTokenView` → JWT(`mid`,`cid`); order links if `Authorization: Customer <jwt>`.
2. Add `PublicCatalogAggregateView` + `<slug>/catalog` route.
3. Frontend `/:slug` parent, `route.params.slug`, slug keys partition, `customer.store` separate.
4. Fix duplicate + remove slug-less paths.

## Alternatives

| Option | Model | Why rejected |
|--------|-------|--------------|
| **B — Global** | One `Customer` global | Breaks isolation, leaks PII |
| **C — Hybrid** | Global + `MerchantCustomer` | Over-engineered, needs ACL, defer SSO |

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `apps/catalog/views_public.py` | Modified | aggregate view |
| `apps/catalog/urls_public.py` | Modified | `<slug>/catalog` |
| `apps/customers/*` | New | Customer model/views/urls |
| `apps/orders/models.py+views.py` | Modified | `customer FK`, parse JWT |
| `config/urls.py` | Modified | dedupe includes |
| `frontend/src/router/index.ts` | Modified | `/:slug/*` routes |
| `frontend/src/views/CatalogView.vue` | Modified | `route.params.slug` |
| `frontend/src/stores/cart.store.ts`, `composables/useMyOrders.ts` | Modified | slug-partitioned keys |
| `frontend/src/stores/customer.store.ts` | New | customer JWT |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Cart/order mixing | High | partition day-1 + test |
| Duplicate URL hides bugs | Med | fix config first |
| Platform/customer JWT confusion | Med | distinct `Customer` prefix |
| Inactive merchant leak | Low | 404 via `_get_merchant_by_slug` |

## Rollback Plan
Gate `CUSTOMER_AUTH_ENABLED`; revert FK then table; guest stays; keep `merchantSlug` fallback until verified.

## Dependencies
- Reuse `simplejwt`; existing `Merchant.slug` helpers.

## Success Criteria
- [ ] `GET /public/<slug>/catalog` isolated
- [ ] `/:slugA` never shows `slugB` cart/myOrders
- [ ] Guest `POST /public/<slug>/orders` works
- [ ] Register/login → customer JWT links order
- [ ] No duplicate `api/public` include

## Open Questions
- [ ] Unique key: phone vs email?
- [ ] OTP verification on register?
- [ ] `/` → default slug or chooser/404?
- [ ] Admin customer list v1 or defer?
