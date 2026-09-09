# Exploration: master-panel (mini panel custom multi-tenant)

## Current State
- Auth is fake: `LoginView.vue` tries 3 token endpoints that do not exist (404); real path is dev bypass writing `dev-token` + `{roles:['ADMIN']}` to localStorage.
- No users app, no `AUTH_USER_MODEL`, no JWT library in `backend/requirements.txt`. All panel views use `AllowAny`; role checks are frontend-only (`:disabled`, `hasAnyRole`).
- Tenant foundation exists: `Merchant` model, fail-closed `for_merchant()` querysets, `TenantContextMiddleware` (X-Merchant-Id, JWT `merchant_id` claim, `/api/public/<slug>`), frontend auto-injects `merchant_slug` + `X-Merchant-Slug`.
- Roles already map to workflow sectors: `TRANSITION_ROLES` in `frontend/src/utils/guards.ts` (TOMA_PEDIDOS>Recepcion, PREPARADOR>Preparacion, CAJERO>Facturacion, REPARTIDOR>Logistica).
- Employee CRUD fixed (fullname/cuil/address/city, roles, PATCH, soft-delete, merchant-filtered list). Branding renamed to Work Zone.
- Security smell: hardcoded dashboard fallback key `dueño123` in `AdminLayout.vue` (was test-only; dies with real auth).

## Affected Areas
- `backend/requirements.txt` — add JWT library
- `backend/apps/tenancy/` — profile, Branch, Merchant seat/branch fields, new endpoints
- `backend/apps/common/middleware.py` — token-bound tenant, master JWT rejection
- `backend/config/settings.py` — JWT wiring
- `frontend/src/stores/auth.store.ts`, `api/client.ts`, `views/LoginView.vue`, router, `layouts/AdminLayout.vue`
- New master panel frontend surface + tests/factories

## Approaches
1. **Extend tenancy app (recommended)** — profile + Branch + Merchant fields there; JWT with merchant_id+role claims. Reuses existing patterns. Effort: Medium.
2. **New users + master apps** — cleaner boundaries, more wiring. Effort: High.
3. **Django admin only** — fastest, insufficient for internal roles + audit. Effort: Low.

## Recommendation
Approach 1, phased: (1) JWT login, (2) operative users CRUD, (3) company onboarding, (4) master panel, (5) sector shared logins + branch filtering, (6) password/session policy. Django admin as stopgap for (3).

## Risks
- Spoofed `merchant_slug` reads other merchants until tenant is token-bound (phase 1 first).
- Seat over-booking races; shared logins weaken audit; scope creep (billing, theming).
- Subagent delegation infra broken (SQLiteError) — phases run inline.

## Ready for Proposal
Yes.
