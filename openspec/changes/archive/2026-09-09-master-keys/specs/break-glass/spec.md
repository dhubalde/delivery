# Break-Glass Specification

## Purpose
Recover the platform when both masters are lost, using the sealed superuser.

## Requirements

### Requirement: Documented recovery path
A runbook MUST describe exact steps: open envelope, log in via Django admin/shell, reset masters, rotate superuser password, reseal. Each step MUST be executable by a technician guided by phone.
#### Scenario: Both masters lost
- GIVEN sealed envelope + technician
- WHEN runbook followed
- THEN masters restored and superuser rotated the same day

### Requirement: Post-use rotation
After ANY break-glass use, the superuser password MUST be rotated and resealed before closing the incident.
#### Scenario: Incident closes
- GIVEN recovery done
- WHEN closing
- THEN old superuser password no longer works
