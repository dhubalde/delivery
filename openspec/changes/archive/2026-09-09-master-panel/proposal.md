# Proposal: Master Panel Custom (multi-tenant identity)

## Intent
Replace fake dev-auth with real JWT identity and add a platform master panel, so N client companies operate isolated on one codebase with licensed seats, each managed by its own ADMIN.

## Scope

### In Scope
- JWT login (simplejwt) with merchant_id+role claims; tenant bound to token, client headers untrusted
- PlatformUser profile: merchant FK (null=master), operative role, branch FK, kind personal/station, must_change_password
- Operative users CRUD, ADMIN-only, backend-enforced; seat_limit (10/20/30) enforced on create
- Merchant onboarding: name/slug/logo + seat_limit + has_branches + first ADMIN creation (atomic)
- Branch model + CRUD (gated by has_branches); users/employees assignable
- Master panel: internal users with role + assigned companies (M2M), companies CRUD, audit log
- Password policy: 8-12 chars, number+upper+special; first-change forced; 180d rotation internals; masters exempt + 2FA; single-use reset tokens (15-30min); session limit per role
- Remove dev bypass + dueño123 fallback

### Out of Scope
- Per-merchant theming/white-label; employee schedules module; billing/payments integration; 2FA implementation detail (deferred to design)

## Capabilities

### New Capabilities
- `platform-auth`: JWT login, claims, tenant binding, logout/session limits
- `operative-users`: users CRUD, roles, seat enforcement, personal/station kinds
- `company-onboarding`: merchant + seats + branches flag + first admin
- `master-panel`: internal users, company assignments, audit log
- `branches`: branch CRUD + assignments
- `password-policy`: complexity, rotation, reset tokens, 2FA requirement

### Modified Capabilities
- `employee-management`: roles move toward User; Employee stays HR record
- `tenant-isolation`: headers untrusted; master JWT rejected on tenant endpoints

## Approach
Extend apps/tenancy (profile, Branch, Merchant fields); simplejwt; backend permissions per endpoint; frontend auth store from server; phased per exploration order.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| backend/requirements.txt | Modified | add simplejwt |
| apps/tenancy/models+serializers+views+urls | Modified | profile, Branch, seat/branch fields, endpoints |
| apps/common/middleware.py | Modified | token-bound tenant, master rejection |
| config/settings.py | Modified | JWT wiring |
| frontend auth store/client/Login/router/AdminLayout | Modified | real tokens, menus, guards |
| master panel frontend | New | internal users, companies, audit views |
| tests/factories | Modified | cover new endpoints |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Cross-merchant read via spoofed slug | High | token-bound tenant first, audit all views |
| Concurrent seat over-booking | Med | DB transaction + check |
| Shared logins weaken audit | Med | station log / shift PIN (design) |
| Scope creep (billing, theming) | Med | explicit out-of-scope list |

## Rollback Plan
Feature-flag JWT auth (fall back to dev bypass), revert migrations in reverse order, keep Employee flow untouched until users CRUD verified.

## Dependencies
- simplejwt package; user roles×levels×actions matrix (user-provided)

## Success Criteria
- [ ] Login returns JWT; tenant endpoints reject spoofed merchant
- [ ] ADMIN-only users CRUD creates user within seat limit
- [ ] Onboarding creates merchant + first ADMIN atomically
- [ ] Master manages companies/users with audit entries
- [ ] No dev bypass or hardcoded keys remain
