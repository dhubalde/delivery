# Company Onboarding Specification

## Purpose
Create a client company with licensed seats, feature flags, and its first ADMIN in one atomic operation.

## Requirements

### Requirement: Atomic company creation
Onboarding MUST create merchant (name, slug, logo) + seat_limit + has_branches + first ADMIN user atomically; any failure MUST roll back everything.
#### Scenario: Happy path
- GIVEN master/internal with company-create permission
- WHEN POST /master/companies with valid payload
- THEN 201 with merchant and its ADMIN credentials setup
#### Scenario: Duplicate slug
- GIVEN an existing slug
- WHEN POST /master/companies with the same slug
- THEN 409 and nothing is created

### Requirement: Seat and branch flags
seat_limit MUST be one of the contracted tiers (10/20/30); has_branches MUST gate the branches module for that company.
#### Scenario: Branches disabled
- GIVEN merchant with has_branches=false
- WHEN accessing branches endpoints or menu
- THEN 403 / hidden menu
