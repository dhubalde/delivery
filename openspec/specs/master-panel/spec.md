# Master Panel Specification

## Purpose
Owner-company backoffice: internal users, client companies, and audit.

## Requirements

### Requirement: Scoped internal users
Internal users MUST have a role (master, admin, dev, tecnico, junior) plus assigned companies (M2M). Non-master callers MUST only see and act on assigned companies; masters bypass scope.
#### Scenario: Unassigned access denied
- GIVEN tecnico assigned to company A
- WHEN GET /master/companies/B/users
- THEN 403
#### Scenario: Admin grant requires seniority
- GIVEN a junior internal user
- WHEN attempting to create another internal user
- THEN 403 (only master or level>=3 per roles matrix)

### Requirement: Audit log
Every master-panel mutation MUST append who, what, which company, and when. The log MUST be append-only (no edit/delete endpoints).
#### Scenario: Company created
- GIVEN a successful onboarding
- WHEN reading /master/audit
- THEN an entry exists with actor, action, company, timestamp

<!-- Merged from change master-keys (2026-09-09) -->
# Delta for master-panel

## ADDED Requirements

### Requirement: Audit session-kill and break-glass usage
Session revocations and any break-glass superuser login MUST appear in the audit log with actor, target, and timestamp.
#### Scenario: Session killed
- GIVEN a revoke call
- WHEN reading /master/audit/
- THEN a SESSION_REVOKED entry exists
