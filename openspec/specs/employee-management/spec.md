# Employee Management Specification (modified)

## Purpose
Employee stays the HR record (personal file for schedules); access roles move to User.

## Requirements

### Requirement: HR-only employee record
Employee MUST hold identity/work data (fullname, cuil, address, city, branch, is_active) and MUST NOT grant system access by itself. Operative roles live on User; EmployeeRole is retained only for future schedule assignment.
#### Scenario: Employee without user
- GIVEN an employee with no linked user
- WHEN they try to log in
- THEN 401 (no credentials exist for them)
#### Scenario: Employee CRUD unchanged
- GIVEN an ADMIN
- WHEN managing employees (create/edit/deactivate)
- THEN current behavior holds (merchant-scoped, soft-delete)

## REMOVED Requirements

### Requirement: EmployeeRole as access control
(Reason: roles move to User with backend enforcement; keeping them as login roles duplicates authority.)
(Migration: EmployeeRole rows preserved for schedule planning; login/kanban guards read User role instead.)
