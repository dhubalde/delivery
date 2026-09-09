# Platform Auth Specification

## Purpose
JWT identity for all Work Zone actors with tenant bound to the token.

## Requirements

### Requirement: JWT login
The system MUST authenticate username+password and return access/refresh tokens whose claims include merchant_id and role. It MUST reject unknown users or wrong passwords with 401 without disclosing which failed.
#### Scenario: Successful login
- GIVEN a registered user with correct password
- WHEN POST /auth/token with credentials
- THEN 200 with access, refresh, and user {username, role, merchant}
#### Scenario: Invalid credentials
- GIVEN wrong password
- WHEN POST /auth/token
- THEN 401 and no token is issued

### Requirement: Token-bound tenant
Protected endpoints MUST resolve merchant_id from the JWT claim and MUST ignore client-supplied merchant_slug/headers for authorization.
#### Scenario: Spoofed slug rejected
- GIVEN a token for merchant A
- WHEN GET /v1/employees with merchant_slug of merchant B
- THEN data is scoped to A (or 403)
#### Scenario: Master token on tenant endpoint
- GIVEN a global master JWT
- WHEN calling any /v1 tenant endpoint
- THEN 403 (masters use master panel only)
