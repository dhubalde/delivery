# Delta for master-panel

## ADDED Requirements

### Requirement: Audit session-kill and break-glass usage
Session revocations and any break-glass superuser login MUST appear in the audit log with actor, target, and timestamp.
#### Scenario: Session killed
- GIVEN a revoke call
- WHEN reading /master/audit/
- THEN a SESSION_REVOKED entry exists
