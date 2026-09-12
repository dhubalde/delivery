# Merchant Catalog Specification

## Purpose
Slug-isolated public catalog aggregate and storefront routing with slug-partitioned client state.

## Requirements

### Requirement: Slug-isolated public catalog aggregate
The system MUST expose `GET /api/public/<slug>/catalog` that returns categories, products, flavors and stats scoped exclusively to the merchant resolved by `<slug>`. The endpoint MUST be `AllowAny` and MUST return 404 for unknown or inactive slugs.

#### Scenario: Aggregate returns merchant catalog
- GIVEN merchant "acme" with active products and categories
- WHEN `GET /api/public/acme/catalog`
- THEN 200 with products, categories, flavors, and stats all belonging to "acme"

#### Scenario: Cross-merchant isolation
- GIVEN merchants "acme" and "beta" with disjoint catalogs
- WHEN `GET /api/public/acme/catalog`
- THEN response MUST NOT contain any entity whose `merchant_id` is "beta"

#### Scenario: Unknown or inactive slug
- GIVEN no active merchant with slug "ghost"
- WHEN `GET /api/public/ghost/catalog`
- THEN 404

#### Scenario: No authentication required
- GIVEN no Authorization header
- WHEN `GET /api/public/acme/catalog`
- THEN 200 (AllowAny)

### Requirement: Slug-based storefront routing and partitioned client state
The SPA MUST mount the storefront under `/:slug` with children `/:slug/checkout` and `/:slug/my-orders`. Cart and myOrders storage MUST be partitioned by slug so state for one slug is never visible under another.

#### Scenario: Slug routing resolves catalog
- GIVEN browser navigates to `/acme`
- WHEN router resolves `route.params.slug`
- THEN CatalogView fetches `/api/public/acme/catalog`

#### Scenario: Cart partitioned by slug
- GIVEN cart contains items for "acme"
- WHEN navigating to `/beta`
- THEN cart for "beta" is empty and `acme` items are not displayed

#### Scenario: MyOrders partitioned by slug
- GIVEN orders cached for "acme"
- WHEN fetching myOrders for "beta"
- THEN only orders created under "beta" are returned/displayed

#### Scenario: Invalid slug shows NotFound
- GIVEN slug does not resolve to an active merchant
- WHEN visiting `/:slug`
- THEN 404 NotFoundView
