# Tasks: Master Panel Custom

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 1500-2500 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 auth → PR2 users → PR3 onboarding → PR4 master → PR5 sectors/branches → PR6 passwords |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | JWT login + token tenant | PR 1 | `pytest apps/tenancy apps/common -q` | login + spoof-slug curl | revert simplejwt wiring, flag off |
| 2 | Operative users CRUD + seats | PR 2 | `pytest apps/tenancy -q -k user` | create user over seat_limit | drop user endpoints |
| 3 | Company onboarding atomic | PR 3 | `pytest apps/tenancy -q -k onboard` | onboard + duplicate slug | drop onboarding endpoint |
| 4 | Master panel + audit | PR 4 | `pytest apps/tenancy -q -k master` | scoped access denied case | drop /master/* |
| 5 | Branches + station logins | PR 5 | `pytest apps/tenancy -q` | branch gate + sector scope | drop branch model |
| 6 | Passwords/sessions + frontend | PR 6 | `npm run test` + pytest | reset flow + eviction | revert Login changes |

## Phase 1: Foundation
- [x] 1.1 Add `djangorestframework-simplejwt` to `backend/requirements.txt`, install, set `SIMPLE_JWT` + `AUTH_V2` flag in `backend/config/settings.py`
- [x] 1.2 Create `PlatformUser`, `Branch`, `AuditEntry` models + `Merchant.seat_limit/has_branches` in `backend/apps/tenancy/models.py`, migrate
- [x] 1.3 Create `backend/apps/common/permissions.py` with `IsAdmin`, `IsMaster`, `HasAssignedCompany`
- [x] 1.4 Extend `backend/apps/tenancy/tests/factories.py` with user/branch/company factories

## Phase 2: Auth + tenant binding
- [x] 2.1 Add `POST /auth/token` issuing merchant_id+role+kind claims; RED test: spoofed slug scoped to token merchant
- [x] 2.2 Modify `backend/apps/common/middleware.py`: token wins, master JWT 403 outside `/master/*`
- [ ] 2.3 Remove dev bypass + `dueño123` fallback from `frontend/src/views/LoginView.vue` and `frontend/src/layouts/AdminLayout.vue`
- [ ] 2.4 Modify `frontend/src/stores/auth.store.ts` + `frontend/src/api/client.ts` to use server tokens/roles

## Phase 3: Users + onboarding + branches
- [x] 3.1 Add `/v1/users/*` CRUD (ADMIN-only, seat check with `select_for_update`, personal/station kinds) in `backend/apps/tenancy/`
- [x] 3.2 Add atomic `POST /master/companies` onboarding endpoint
- [x] 3.3 Add `/v1/branches/*` CRUD gated by `has_branches`
- [x] 3.4 Add `/master/*` internal users, assignments, append-only audit endpoints

## Phase 4: Frontend wiring
- [x] 4.1 Create `frontend/src/views/admin/AdminUsersView.vue` + API/composable, role-gated menu entries
- [x] 4.2 Create `/master` section: companies, internal users, audit views
- [x] 4.3 Add first-change-password + reset-request/confirm flows to login
- [x] 4.4 Station users see only their sector columns (kanban scope)

## Phase 5: Policy + verification
- [x] 5.1 Implement complexity/rotation/expiry, reset tokens (15-30min, single-use), session caps with eviction
- [x] 5.2 Integration tests per spec scenario (mismatch 403, seat 409, reset burn 410, eviction)
- [x] 5.3 Verify full flow: onboard → login → create users → reset → audit entries
