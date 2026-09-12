# Delta for tenant-isolation

## ADDED Requirements

### Requirement: Public slug isolation (AllowAny)
Public endpoints under `/api/public/<slug>/*` MUST be `AllowAny` and MUST scope all queries exclusively by the merchant resolved from `<slug>` via `_get_merchant_by_slug`. They MUST NOT require a Work Zone JWT and MUST NOT leak data from other merchants.

#### Scenario: Public catalog isolated by slug
- GIVEN merchants "acme" and "beta"
- WHEN `GET /api/public/acme/products`
- THEN response contains only products where merchant slug is "acme"

#### Scenario: Inactive merchant on public endpoint
- GIVEN merchant "acme" is inactive
- WHEN `GET /api/public/acme/catalog`
- THEN 404

#### Scenario: Customer endpoints scoped by slug
- GIVEN customer JWT for "acme"
- WHEN calling any `/api/public/beta/*` with that JWT
- THEN 401/403 and no data from "beta" is returned

### Requirement: Deduplicated public URL configuration
The system MUST define each `api/public/<slug>/orders` route exactly once in `config/urls.py` via a namespaced include, and MUST remove the duplicate bare and nested includes that shadow slug resolution.

#### Scenario: No duplicate public include
- GIVEN `config/urls.py` is inspected
- WHEN counting `include("apps.orders.urls_public")`
- THEN exactly one slug-prefixed entry exists for orders and zero bare `api/public/` duplicate

#### Scenario: Root public orders without slug is not reachable
- GIVEN `apps.orders.urls_public` still defines legacy `""` path
- WHEN `POST /api/public/orders` (no slug)
- THEN 404 (slug is required after dedup)

#### Scenario: Catalog and orders share consistent slug prefix
- GIVEN `apps.catalog.urls_public` and `apps.orders.urls_public`
- WHEN requesting `/api/public/acme/catalog` and `/api/public/acme/orders`
- THEN both resolve under the same `api/public/<slug>/` prefix
