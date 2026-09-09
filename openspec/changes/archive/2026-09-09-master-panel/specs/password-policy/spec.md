# Password Policy Specification

## Purpose
Credential rules, rotation, recovery, and session limits for all actor levels.

## Requirements

### Requirement: Complexity and first change
Passwords MUST be 8-12 chars with at least one number, one uppercase, one special char. New users MUST change the initial password on first login (must_change_password flag blocks all other actions until done).
#### Scenario: Weak password rejected
- GIVEN password "caja123"
- WHEN setting it
- THEN 422 (missing uppercase and special)
#### Scenario: First login forces change
- GIVEN user with must_change_password=true
- WHEN calling any endpoint except password-change
- THEN 403 PASSWORD_CHANGE_REQUIRED

### Requirement: Rotation and master exemption
Internal users MUST rotate every 180 days; operatives MUST NOT be forced to rotate; the 2 master passwords MUST never expire (compensated by strong password + 2FA).
#### Scenario: Expired internal password
- GIVEN internal password older than 180 days
- WHEN logging in
- THEN 403 PASSWORD_EXPIRED with change flow

### Requirement: Assisted recovery
Resets MUST use single-use tokens expiring in 15-30 min, approved by the company ADMIN (operatives) or another master (internal/master; nobody resets self). Every reset MUST be audit-logged.
#### Scenario: Operative forgets password
- GIVEN an ADMIN-generated reset token
- WHEN POST reset with a compliant new password within 20 min
- THEN 200 and token is burned (reuse gives 410)

### Requirement: Session limits
Concurrent sessions MUST be capped per role (operatives 2, internals 3); exceeding the cap MUST evict the oldest session and notify.
#### Scenario: Third device
- GIVEN operative with 2 active sessions
- WHEN logging in on a third device
- THEN oldest session is revoked
