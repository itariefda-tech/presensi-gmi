# Deployment Checklist

## Security

- Set `FLASK_SECRET`.
- Disable debug mode in production.
- Use HTTPS behind a reverse proxy.
- Configure secure session cookies at deployment layer.
- Keep CSRF enabled.
- Confirm password reset delivery settings.
- Confirm owner add-on password is configured.

## Database

- Run `_init_db()` migration on startup.
- Back up SQLite before release.
- Confirm Phase 16 tables exist: `roles`, `permissions`, `user_scopes`, `retention_policies`, `login_attempts`.
- Confirm enterprise indexes exist for attendance, leave, audit, billing, contract.

## Application Smoke Test

- Login with admin.
- Login rate-limit rejects repeated failed login attempts.
- Employee checkin/checkout.
- Leave request and approval.
- Payroll generation.
- Client subscription update.
- Contract and billing config update.
- Client billing summary renders.

## Operations

- Review `audit_logs` after admin actions.
- Monitor database size.
- Review retention policy before enabling cleanup automation.
- Keep upload directory backed up or moved to object storage before scaling.
