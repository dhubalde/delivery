# Design: Master Keys Custody & Recovery

## Technical Approach
Small additive slice on shipped master-panel: widen reset-target query, add session list/revoke endpoints reusing SessionRecord, revoke-all hook on reset issue, and a repo runbook doc. No migrations expected.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|---|---|---|---|
| Reset-target lookup | Q(profile merchant null) OR (no profile + superuser) | force profile creation | break-glass accounts are born via createsuperuser |
| Revoke-all placement | inside reset-request (both scopes) | only on confirm | compromised sessions must die at issue time |
| Session list scope | master: any; ADMIN: own merchant users | global list | least privilege, matches audit scoping |
| Runbook location | repo doc `docs/break-glass.md` | wiki/outside | travels with code, versioned |

## Data Flow

    Reset request ──→ revoke all target sessions ──→ issue single-use token ──→ audit
    Session kill ──→ revoke jti ──→ 401 on next use ──→ audit SESSION_REVOKED
    Break-glass ──→ sealed envelope ──→ shell/admin ──→ rotate + reseal ──→ audit

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/apps/tenancy/views.py` | Modify | reset-target Q fix, revoke-all hook, session list/revoke views |
| `backend/apps/tenancy/urls.py`, `config/urls.py` | Modify | session routes (tenant + master) |
| `backend/apps/tenancy/tests/test_master_keys.py` | Create | reset superuser, revoke-all, session-kill tests |
| `frontend/src/views/master/*` | Modify | sessions UI (minimal list + revoke button) |
| `docs/break-glass.md` | Create | ceremony, recovery, offboarding runbook |

## Interfaces / Contracts
- `GET /v1/users/<id>/sessions/` → `[{jti_prefix, created_at, active}]` (ADMIN, own merchant)
- `POST /v1/users/<id>/sessions/revoke/` → `{revoked: n}` + audit
- `GET /api/master/sessions/?username=` + `POST /api/master/sessions/revoke/` (master scope)
- Reset issue now returns 200 and revokes target sessions first

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Integration (pytest) | superuser reset, revoke-all on issue, kill → 401 | APIClient |
| Manual | runbook dry-run (read-through, no execution) | checklist sign-off |

## Threat Matrix
N/A — no shell, subprocess, VCS/PR, executable, or process-integration boundary. New HTTP routes covered by existing tenant/master guards.

## Migration / Rollout
No migration expected. Docs-only runbook ships with code.

## Open Questions
- [ ] Exact wording of custodian instruction card (owner writes, tech reviews)
