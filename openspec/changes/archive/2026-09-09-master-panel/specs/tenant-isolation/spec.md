# Tenant Isolation Specification (modified)

## Purpose
Tenant is proven by the token, never by client-sent values.

## Requirements

### Requirement: Token-bound merchant scope
Every tenant endpoint MUST scope by the JWT merchant_id claim. Client-sent merchant_slug/headers MAY remain as a consistency check but MUST NOT authorize.
#### Scenario: Slug/token mismatch
- GIVEN token for merchant A with slug of B
- WHEN calling a tenant endpoint
- THEN 403 TENANT_MISMATCH
#### Scenario: Missing or invalid token
- GIVEN no token on a protected endpoint
- WHEN calling it
- THEN 401 (fail-closed; no merchant inference)

### Requirement: Master containment
Global master JWTs MUST be rejected on all tenant endpoints (403); they are valid only on /master/* routes.
#### Scenario: Master reads tenant data
- GIVEN master token
- WHEN GET /v1/orders of any merchant
- THEN 403 (support access goes through master routes with audit)
