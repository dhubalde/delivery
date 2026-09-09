# Design: Master Panel Custom

## Technical Approach
Extend `apps/tenancy` with identity models, issue JWTs carrying tenant claims, bind every tenant queryset to the token (never to client headers), and add a `/master/*` surface plus panel views. Roll out in 6 phases behind an `AUTH_V2` flag so the current Employee flow keeps working until users CRUD is verified.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|---|---|---|---|
| JWT library | djangorestframework-simplejwt | custom HMAC tokens | standard rotation/revocation, less crypto to own |
| Identity model | `PlatformUser` OneToOne to Django User | custom AUTH_USER_MODEL | zero rewrite of auth admin; Employee untouched |
| App placement | extend `apps/tenancy` | new users/master apps | reuses for_merchant, middleware, serializer patterns |
| Master surface | same deploy, `/master/*` API + `/master` frontend section | separate service | v1 speed; split later if needed |
| Seat check | `select_for_update` on Merchant + count in transaction | app-level count | closes concurrent over-booking race |
| Passwords | Django `make_password` only | custom hashing | never roll own crypto |
| 2FA | TOTP (phase 6), masters+internals required | SMS/hardware now | TOTP is free, offline, enough for v1 |

## Data Flow

    Login ──→ simplejwt + claims (merchant_id, role, kind) ──→ access JWT
      │
      ▼
    TenantContextMiddleware ──→ ContextVar merchant (token wins; headers ignored for authz)
      │
      ▼
    Views: for_merchant(token_mid) ──→ 403 on mismatch; master JWT 403 outside /master/*
      │
    Audit middleware ──→ append-only log (actor, action, company, ts)

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/requirements.txt` | Modify | add simplejwt (+ OTP lib phase 6) |
| `apps/tenancy/models.py` | Modify | PlatformUser, Branch, Merchant.seat_limit/has_branches, AuditEntry |
| `apps/tenancy/serializers.py` | Modify | user/branch/company serializers, seat validation |
| `apps/tenancy/views.py`, `urls.py` | Modify | /auth/*, /v1/users/*, /v1/branches/*, /master/* |
| `apps/common/middleware.py` | Modify | token-bound tenant, master rejection |
| `apps/common/permissions.py` | Create | IsAdmin, IsMaster, HasAssignedCompany |
| `config/settings.py` | Modify | SIMPLE_JWT, AUTH_V2 flag |
| `frontend/src/stores/auth.store.ts`, `api/client.ts` | Modify | real tokens, server user/roles |
| `frontend/src/views/LoginView.vue` | Modify | real login, first-change, reset; delete dev bypass |
| `frontend/src/router/index.ts`, layouts | Modify | /master section, role-gated menus, Users/Branches entries |
| `frontend/src/views/master/*`, `views/admin/AdminUsersView.vue`... | Create | master + users + branches views |
| tests/factories + new tests | Modify | per-phase coverage |

## Interfaces / Contracts
- `POST /auth/token {username,password}` → `{access, refresh, user{username,role,merchant,must_change_password}}`
- JWT claims: `merchant_id (nullable=master)`, `role`, `kind`, `branch_id?`
- Errors: `TENANT_MISMATCH 403`, `SEAT_LIMIT_REACHED 409`, `PASSWORD_CHANGE_REQUIRED 403`, `PASSWORD_EXPIRED 403`
- Reset: `POST /v1/users/reset-request` → single-use token (15-30min) → `POST /v1/users/reset-confirm`

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit (pytest) | seat check, validators, permissions | factories, no HTTP |
| Integration (pytest) | login→claims, spoof rejection, onboarding atomicity, reset burn | APIClient per phase |
| Frontend (vitest) | guards, menus by role, first-change flow | component tests |

## Threat Matrix
N/A — no shell, subprocess, VCS/PR automation, executable classification, or process-integration boundary. New HTTP routes are covered by tenant-isolation spec (spoof/mismatch RED tests propagate to tasks).

## Migration / Rollout
Phases 1-6 sequential; AUTH_V2 flag keeps dev bypass until phase 2 verified; migrations additive only (new tables + nullable columns); EmployeeRole kept read-only for schedules.

## Open Questions
- [ ] Roles×levels×actions matrix (user-provided) fixes permission details
- [ ] Shift-PIN vs shared credential for station audit trail
- [ ] TOTP library choice (django-otp vs other) at phase 6
