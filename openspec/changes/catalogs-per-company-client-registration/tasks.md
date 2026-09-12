# Tasks: Catalogs per Company & Client Registration

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 550–700 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 Foundation → PR2 Backend → PR3 Frontend |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Duplicate fix + Customer model + Order.customer FK | PR1 | `python manage.py test apps.customers apps.orders` | `GET /ghost/catalog→404`; `POST /public/orders→404` | Revert `config/urls.py` + drop FK/table |
| 2 | Catalog aggregate + scoped JWT + order link | PR2 | `python manage.py test apps.catalog apps.customers` | `GET /acme/catalog` isolated; `POST /register→201` | Revert `apps/customers/*` + catalog view |
| 3 | `/:slug` routing + partitioned stores + header | PR3 | `npm run test -- stores router` | `/acme` vs `/beta` isolated | Revert `router/index.ts` + `customer.store.ts` |

## Phase 1: Foundation

- [x] 1.1 Fix `backend/config/urls.py` — single `api/public/<slug:slug>/` include; remove duplicate bare/double slug. Spec: dedup/root 404/prefix.
- [x] 1.2 Create `backend/apps/customers/models.py` — `Customer(merchant FK, phone, name, password_hash)` + `UniqueConstraint(merchant,phone)`. Add `customers` to apps. Spec: unique/cross-merchant.
- [x] 1.3 Add `customer FK (SET_NULL)` to `backend/apps/orders/models.py` + migration. Spec: Order.customer.
- [x] 1.4 RED — duplicate shadows slug: `POST /public/orders→404` vs `POST /public/acme/orders→201` (threat: duplicate).

## Phase 2: Backend

- [ ] 2.1 Add `PublicCatalogAggregateView` in `backend/apps/catalog/views_public.py` + `<slug>/catalog` in `backend/apps/catalog/urls_public.py` — `AllowAny` via `_get_merchant_by_slug`→404. Spec: aggregate/404/AllowAny.
- [ ] 2.2 Create `backend/apps/customers/auth.py` + `views.py` (register/login/me) + `urls_public.py` `<slug>/customers/*`; SimpleJWT `mid/cid`, header `Customer`. Spec: register/login/me + JWT.
- [ ] 2.3 Modify `backend/apps/orders/views.py` — parse `Customer` JWT; `mid==slug`→link else guest (no fail). Spec: guest/auth/mismatched.
- [ ] 2.4 RED — AllowAny: `GET /public/acme/catalog` no auth→200; `POST /public/acme/orders` guest→201 (threat: Bearer).
- [ ] 2.5 RED — prefix: `Bearer` on `customers/me`→401 vs `Customer`→200 (threat: prefix).
- [ ] 2.6 RED — inactive: `GET /public/inactive/catalog`→404 (threat: inactive).
- [ ] 2.7 RED — cross-merchant: `GET /public/acme/catalog` excludes beta (threat: slug leak).

## Phase 3: Frontend

- [ ] 3.1 Modify `frontend/src/router/index.ts` — `/:slug` with `checkout`/`my-orders`; invalid→`NotFoundView`. Spec: slug routing/invalid.
- [ ] 3.2 Create `frontend/src/stores/customer.store.ts` — keys `customer:{slug}`, `register/login/me/logout`. Spec: isolation.
- [ ] 3.3 Modify `frontend/src/stores/cart.store.ts` (`cart:{slug}`) + `frontend/src/composables/useMyOrders.ts` (`myOrders:{slug}`) + `frontend/src/api/client.ts` attach `Customer` header. Spec: cart/myOrders partition.
- [ ] 3.4 Modify `frontend/src/views/CatalogView.vue` — `slug=route.params.slug`, fetch `/api/public/{slug}/catalog`, 404→NotFound.

## Phase 4: Verification

- [ ] 4.1 Unit: constraint, password, JWT `mid/cid`, mismatch→403 (`python manage.py test`).
- [ ] 4.2 Integration: catalog isolation, guest/auth/mismatched (`APITestCase`).
- [ ] 4.3 Frontend Vitest: router `/:slug` + cart/myOrders/customer two-slug (`npm run test`).
- [ ] 4.4 Smoke: `/acme` catalog, `/acme/checkout` guest, register→linked order, `/beta` empty, `POST /public/orders`→404.

## Phase 5: Cleanup

- [ ] 5.1 Remove `backend/apps/orders/urls_public.py` legacy `""`/`"/"`; gate `CUSTOMER_AUTH_ENABLED`.
- [ ] 5.2 Document slug API; rollback note (drop FK then table).
