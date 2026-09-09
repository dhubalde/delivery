# Session Kill Specification

## Purpose
List and revoke active sessions without changing passwords.

## Requirements

### Requirement: List own and subordinate sessions
Masters MUST list any user's sessions; company ADMINs MUST list their users' sessions. Each entry shows device hint (jti prefix), creation, and active/revoked state.
#### Scenario: Admin reviews sessions
- GIVEN an ADMIN
- WHEN GET sessions of a cashier
- THEN active sessions listed, other companies excluded

### Requirement: Revoke session
Revoking MUST immediately invalidate the token (401 SESSION_REVOKED) and audit the action.
#### Scenario: Stolen session killed
- GIVEN a compromised active session
- WHEN revoked by master/admin
- THEN next call with that token gets 401
