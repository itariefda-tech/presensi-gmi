# RBAC Matrix

Phase 16 introduces canonical RBAC tables:

- `roles`
- `permissions`
- `role_permission_map`
- `user_scopes`

## Scope Types

- `GLOBAL`: all clients/sites.
- `CLIENT`: one client.
- `SITE`: one site.
- `SELF`: own employee data.

## Role Scope

| Role | Default Scope |
| --- | --- |
| owner | GLOBAL |
| hr_superadmin | GLOBAL |
| admin_asistent | GLOBAL |
| manager_operational | GLOBAL |
| client_admin | CLIENT |
| client_assistant | CLIENT |
| client_supervisor | SITE |
| supervisor | SITE |
| finance | CLIENT |
| auditor | GLOBAL |
| employee | SELF |

## Permission Groups

| Group | Permissions |
| --- | --- |
| Attendance | `attendance.view`, `attendance.export`, `attendance.approve` |
| Payroll | `payroll.view`, `payroll.process`, `payroll.export` |
| Billing | `billing.view`, `billing.config.update` |
| Contract | `contract.view`, `contract.manage` |
| Patrol | `patrol.view`, `patrol.create`, `patrol.review` |
| Employee | `employee.view`, `employee.manage` |
| Site | `site.view`, `site.manage` |
| Audit | `audit.view` |
| Settings | `settings.manage` |

## Enforcement Notes

Existing route guards remain role-based for compatibility. New RBAC tables are seeded and ready for progressive route-level enforcement without breaking current admin/client flows.
