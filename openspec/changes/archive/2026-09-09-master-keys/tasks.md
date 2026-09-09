# Tasks: Master Keys Custody & Recovery

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 150-250 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | single-pr |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: single-pr
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Reset fix + session-kill + revoke-all + runbook | single PR | `pytest apps/tenancy -q -k "master or password or session or reset"` | reset superuser + kill live session via shell | revert view/url/test/doc hunks |

## Phase 1: Backend
- [x] 1.1 Fix `MasterResetRequestView` target lookup: profile-less superuser included (Q query)
- [x] 1.2 Revoke all target sessions inside `_issue_reset_token` callers (tenant + master)
- [x] 1.3 Add session list/revoke endpoints (tenant scoped + master scoped) with audit entries
- [x] 1.4 Write `backend/apps/tenancy/tests/test_master_keys.py` (reset superuser, revoke-all, kill → 401)

## Phase 2: Docs + UI
- [x] 2.1 Write `docs/break-glass.md` (ceremony, recovery, offboarding, instruction card template)
- [x] 2.2 Minimal sessions UI in master views (list + revoke button)

## Phase 3: Verification
- [x] 3.1 Run focused + full backend suites; confirm only pre-existing failures remain
