# Operative Users Specification

## Purpose
Company-scoped system users (personal or shared station logins), managed only by ADMIN.

## Requirements

### Requirement: ADMIN-only management
User create/update/deactivate endpoints MUST require ADMIN role of the same merchant; non-ADMIN callers get 403. Granting ADMIN MUST show an explicit warning and require confirmation.
#### Scenario: Cajero tries to create a user
- GIVEN a CAJERO token
- WHEN POST /v1/users
- THEN 403
#### Scenario: Granting ADMIN
- GIVEN an ADMIN creating a user with role ADMIN
- WHEN confirming the warning
- THEN user is created and the grant is audit-logged

### Requirement: Seat enforcement
Creating a user MUST fail with 409 when the merchant already has seat_limit active users. Deactivated users MUST NOT count toward the limit.
#### Scenario: Limit reached
- GIVEN merchant with seat_limit 10 and 10 active users
- WHEN POST /v1/users
- THEN 409 SEAT_LIMIT_REACHED

### Requirement: Personal or station kind
A user MUST be kind personal (one employee) or station (shared login bound to a workflow sector). Station users MUST be restricted to their sector's kanban columns.
#### Scenario: Station login scope
- GIVEN station user for PREPARACION
- WHEN advancing an order from LOGISTICA
- THEN 403 (outside its sector)
