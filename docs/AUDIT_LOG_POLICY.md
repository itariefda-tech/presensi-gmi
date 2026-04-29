# Audit Log Policy

## Table

`audit_logs`

Enterprise fields:

- `actor_user_id`
- `client_id`
- `action`
- `entity_type`
- `entity_id`
- `before_json`
- `after_json`
- `ip_address`
- `user_agent`
- `created_at`

Legacy compatibility fields remain:

- `actor_email`
- `branch_id`
- `actor_role`
- `summary`
- `details_json`

## Events To Log

- Login success
- Attendance approval/rejection
- Leave approval/rejection
- Employee create/update/delete
- Client/site create/update/delete
- Billing add-on/package updates
- Contract updates
- Billing config updates
- Payroll generation/approval

## Retention

Default retention: 5 years, controlled by `retention_policies` entry `audit_logs`.

## Privacy

Avoid storing raw passwords, tokens, or full uploaded file contents in audit logs. Store references, summaries, and before/after JSON only for business fields.
