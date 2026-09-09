# Proposal: Master Keys Custody & Recovery

## Intent
Harden the 2 master keys' lifecycle: creation ceremony, compromise response, break-glass via sealed Django superuser, and fix reset-target gap — while the owner is the sole custodian.

## Scope

### In Scope
- Fix: superuser-without-profile resettable by another master via endpoint
- Session-kill: list active sessions + revoke (without password change)
- Revoke-all-sessions on any reset issue (tenant + master)
- Creation ceremony: superuser creates 2 masters, sealed envelope in safe (credentials + instruction card for non-technical custodians: owner + siblings)
- Break-glass runbook: superuser-only recovery when both masters fall (steps, audit, post-use rotation)
- Rule: superuser never used operationally; any login = incident + rotation
- Offboarding checklist: revoke, rotate, remove assignments

### Out of Scope
- TOTP implementation (planned phase 6 of master-panel)
- Quorum/dual-approval flows (deferred until company grows)
- HSM/hardware keys, SSO

## Capabilities

### New Capabilities
- `master-custody`: creation ceremony, sealed storage, custodian instruction card
- `session-kill`: list/revoke active sessions per user
- `break-glass`: superuser recovery runbook + post-use rotation

### Modified Capabilities
- `password-policy`: reset endpoints cover profile-less superusers; revoke-all on issue
- `master-panel`: audit covers session-kill + break-glass usage

## Approach
Small backend slice (query fix, session endpoints, revoke hooks) + runbook docs. No schema changes except possibly session metadata.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| apps/tenancy/views.py | Modified | reset-target fix, session-kill endpoints, revoke hooks |
| frontend master views | Modified | session list/revoke UI (minimal) |
| docs/runbook | New | ceremony + break-glass + offboarding (repo file) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Break-glass envelope misused/lost | Low | sealed, access log, rotation after any use |
| Non-technical custodian confusion | Med | instruction card with exact call script |
| Scope creep to quorum/SSO | Med | explicit out-of-scope list |

## Rollback Plan
Revert endpoint hunks; runbook is docs-only. No migrations expected.

## Dependencies
- master-panel shipped (done, archived 2026-09-09)

## Success Criteria
- [ ] Profile-less superuser resettable by another master
- [ ] Active sessions listable and revocable; reset revokes all
- [ ] Runbook exists: ceremony, break-glass, offboarding
- [ ] Tests cover reset-target fix + session-kill
