# Master Custody Specification

## Purpose
How the 2 master keys are born, stored, and retired while the owner is sole custodian.

## Requirements

### Requirement: Sealed creation ceremony
Masters MUST be created by the break-glass superuser; the superuser password MUST then be sealed in an envelope in the safe with an instruction card for non-technical custodians (owner + siblings: who to call, exact script, do nothing else).
#### Scenario: Ceremony completes
- GIVEN a fresh install
- WHEN superuser creates 2 masters and seals the envelope
- THEN both masters log in and the superuser is never used again

### Requirement: No operational use
The break-glass superuser MUST NOT be used for daily ops; any login MUST be treated as incident, audited, and followed by rotation.
#### Scenario: Superuser login detected
- GIVEN a superuser login outside ceremony/recovery
- WHEN audit is reviewed
- THEN it appears flagged and rotation is due

### Requirement: Offboarding checklist
Removing a master MUST revoke sessions, rotate shared secrets they knew, and remove assignments in one flow.
#### Scenario: Master leaves
- GIVEN offboarding run
- WHEN completed
- THEN zero active sessions and no assignments remain
