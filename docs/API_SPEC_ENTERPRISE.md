# API Spec Enterprise

## Auth

- `POST /api/auth/login`
  - Body: `identifier`, `email`, atau `phone`, `password`, `login_type`
  - Security: persistent rate limit via `login_attempts`

- `POST /api/auth/forgot`
- `POST /api/auth/reset_password`

## Attendance

- `POST /api/attendance/checkin`
- `POST /api/attendance/checkout`
- `GET /api/attendance/today`
- `GET /api/attendance/summary`
- `POST /api/attendance/manual`
- `POST /api/attendance/approve`
- `POST /api/attendance/reject`

## Reports

- `GET /api/reports/attendance`
- `GET /api/reports/late`
- `GET /api/reports/absent`
- `GET /api/reports/summary`

## Leave

- `POST /api/leave/create`
- `POST /api/leave/request`
- `GET /api/leave/my`
- `GET /api/leave/pending`
- `POST /api/leave/approve`
- `POST /api/leave/reject`

## Payroll

- `POST /api/payroll/generate`
- `GET /api/payroll/history`
- `POST /api/payroll/approve`
- `GET /api/payroll/export`

## Owner & Settings

- `GET /api/owner/addons`
- `POST /api/owner/addons/verify`
- `POST /api/owner/addons`
- `POST /dashboard/admin/settings/subscription/update`

## Enterprise Billing & Contract

- `POST /dashboard/admin/clients/<client_id>/contract/save`
- `POST /dashboard/admin/clients/<client_id>/billing/save`
- Read-only billing summary is rendered in Client Profile.

## Security Notes

- Form POST uses CSRF token.
- JSON POST uses `X-CSRF-Token` or `csrf_token` body when a session user exists.
- API access routes use add-on gating where applicable.
