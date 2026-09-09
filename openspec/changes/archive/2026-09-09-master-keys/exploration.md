# Exploration: master-keys (custodia y recupero de llaves master)

## Current State
- Masters exist as: superuser without profile, or PlatformUser(merchant=None, role=MASTER). Claims carry merchant_id=None; middleware 403s them on tenant paths.
- Reset flows: MasterResetRequestView (another master, no self-reset), change-password endpoint, single-use 20-min tokens, session caps with eviction.
- Gaps found: superuser-without-profile is NOT resettable via endpoint (filter requires profile); no explicit session-kill; no documented creation ceremony; no break-glass for both-compromised; TOTP deferred.
- Audit exists (INTERNAL_USER_CREATED/UPDATED, PASSWORD_RESET_ISSUED/USED, COMPANY_ONBOARDED).

## Threat Scenarios
1. **1 clave robada (phishing)** — otro master revoca sesiones + resetea. Needs: session-kill endpoint, fast path.
2. **Master desvinculado** — revoke + rotate + remove assignments. Needs: offboarding checklist.
3. **Las 2 comprometidas** — no queda nadie adentro. Needs: break-glass server-side (shell + SECRET_KEY/Infrastructure access). Who holds server access?
4. **Insider malicioso** — un master actúa mal. Needs: audit alerts, quorum for critical actions (e.g., creating another master requires... both?).
5. **Pérdida total de acceso** — olvido + pierde 2FA. Needs: recovery without self-reset (in-person ceremony?).
6. **Token/sesión robada** — kill session without password change. Needs: session list + revoke.
7. **Creación inicial** — where, who witnesses, where stored (password manager? sealed envelope?).

## Approaches
1. **Policy + minimal endpoints (recommended)** — creation ceremony doc, session-kill + revoke-on-reset, fix reset-target bug, break-glass runbook, audit alerts. Effort: Medium.
2. **Quorum/MFA-hardened** — TOTP mandatory now, dual-approval for master creation. Effort: High.
3. **Externalize** — SSO/hardware keys. Effort: High, premature.

## Recommendation
Approach 1 now; TOTP (already planned phase 6) as the 2FA leg; quorum rule (both masters to create third) as policy.

## Risks
- Break-glass needs server access holder defined, else scenario 3 is unrecoverable.
- Shared/station logins weaken attribution during incidents.

## Ready for Proposal
Yes — after user adds scenarios.
