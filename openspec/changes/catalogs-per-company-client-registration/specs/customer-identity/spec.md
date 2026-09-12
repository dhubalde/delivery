# Customer Identity Specification

## Purpose
Per-merchant buyer identity isolated by merchant, with scoped Customer authentication and guest checkout coexistence.

## Requirements

### Requirement: Merchant-scoped Customer entity
The system MUST persist `Customer` with `merchant` FK, `phone`, `name`, and `password_hash`. The pair `(merchant, phone)` MUST be unique. Same phone number on different merchants MUST create independent Customer rows.

#### Scenario: Unique phone per merchant
- GIVEN merchant "acme" already has customer phone "555-1000"
- WHEN registering phone "555-1000" for "acme" again
- THEN 409 Conflict (duplicate)

#### Scenario: Same phone across merchants allowed
- GIVEN customer phone "555-1000" exists for merchant "acme"
- WHEN registering phone "555-1000" for merchant "beta"
- THEN 201 Created for "beta"

#### Scenario: Order links to Customer FK
- GIVEN an authenticated customer order
- WHEN order is created
- THEN `Order.customer` references the Customer and `Order.merchant` equals `Customer.merchant`

### Requirement: Customer registration and authentication per slug
The system MUST expose `POST /api/public/<slug>/customers/register`, `/login`, and `GET /api/public/<slug>/customers/me` scoped by `<slug>`. On success, `register` and `login` MUST return a JWT with claims `mid` (merchant id) and `cid` (customer id) signed separately from Work Zone tokens; the JWT MUST be sent as `Authorization: Customer <jwt>`. Endpoints MUST be `AllowAny` except `me` which requires the Customer JWT.

#### Scenario: Register creates customer and returns JWT
- GIVEN merchant "acme" active with no customer phone "555-2000"
- WHEN `POST /api/public/acme/customers/register` with name, phone, password
- THEN 201 with access/refresh tokens containing `mid=acme.id` and `cid=newCustomer.id`

#### Scenario: Login returns scoped JWT
- GIVEN customer exists for "acme" with correct password
- WHEN `POST /api/public/acme/customers/login` with phone and password
- THEN 200 with JWT scoped to "acme" and `cid` of that customer

#### Scenario: Login with wrong password
- GIVEN correct phone but wrong password
- WHEN `POST /api/public/acme/customers/login`
- THEN 401 without token, no leak of existence

#### Scenario: Me returns profile for valid Customer token
- GIVEN valid `Authorization: Customer <jwt>` for customer of "acme"
- WHEN `GET /api/public/acme/customers/me`
- THEN 200 with customer {name, phone, merchant slug}

#### Scenario: Cross-merchant JWT rejected
- GIVEN Customer JWT with `mid=acme.id`
- WHEN `GET /api/public/beta/customers/me` with that JWT
- THEN 403 or 401 (merchant mismatch, token not valid for beta)

#### Scenario: Frontend customer store isolation
- GIVEN customer logged in for "acme"
- WHEN navigating to `/beta`
- THEN customer store for "beta" is unauthenticated (separate key, no leakage)

### Requirement: Guest checkout coexists with customer auth
`POST /api/public/<slug>/orders` MUST succeed without a Customer JWT (guest). When a valid `Authorization: Customer <jwt>` is present and its `mid` matches `<slug>`, the order MUST be linked to that Customer; otherwise the order MUST be created as guest and MUST NOT fail.

#### Scenario: Guest order succeeds
- GIVEN no Customer JWT
- WHEN `POST /api/public/acme/orders` with valid order payload
- THEN 201 guest order with `customer` null

#### Scenario: Authenticated order links customer
- GIVEN valid Customer JWT for "acme"
- WHEN `POST /api/public/acme/orders` with `Authorization: Customer <jwt>`
- THEN 201 order with `customer` set to that Customer

#### Scenario: Mismatched Customer token does not block guest
- GIVEN Customer JWT for "beta" but posting to `/api/public/acme/orders`
- WHEN `POST /api/public/acme/orders` with that JWT
- THEN either 403 or guest order created without customer link (no cross-merchant link)
