# Delta for password-policy

## ADDED Requirements

### Requirement: Reset covers profile-less superusers
Master reset MUST also match active superusers without a platform profile (break-glass accounts created via createsuperuser).
#### Scenario: Reset a profile-less master
- GIVEN superuser "root" with no profile
- WHEN another master requests reset for "root"
- THEN 200 with a single-use token

### Requirement: Revoke-all on reset issue
Issuing a reset (tenant or master) MUST revoke all active sessions of the target user immediately.
#### Scenario: Hacked user reset
- GIVEN an active session of a compromised user
- WHEN admin issues a reset
- THEN that session gets 401 on next call
