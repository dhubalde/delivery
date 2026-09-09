# Branches Specification

## Purpose
Optional physical branches per company to group users and employees.

## Requirements

### Requirement: Gated branch CRUD
Branch endpoints MUST require the merchant's has_branches flag; ADMIN of the merchant manages branches; users/employees MAY be assigned to a branch.
#### Scenario: Assign user to branch
- GIVEN an operative user and a branch of the same merchant
- WHEN PATCH /v1/users/{id} with branch
- THEN 200 and user is branch-scoped
#### Scenario: Cross-merchant branch rejected
- GIVEN a branch of merchant A
- WHEN assigning a user of merchant B to it
- THEN 422 (branch and user MUST share merchant)
