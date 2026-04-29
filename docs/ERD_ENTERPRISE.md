# ERD Enterprise

Dokumen ini merangkum tabel enterprise utama setelah Phase 16.

## Core Tenant

- `clients`: tenant/client utama.
- `sites`: lokasi milik client, terhubung lewat `sites.client_id`.
- `users`: akun sistem, dapat membawa `client_id`, `site_id`, atau `branch_id`.
- `employees`: data pegawai, terhubung ke `client_id` dan `site_id`.
- `assignments`: penempatan pegawai ke site/client dalam rentang tanggal.

## Attendance, Leave, Payroll

- `attendance`: record checkin/checkout, scoped by `client_id` dan `branch_id`.
- `manual_attendance_requests`: pengajuan koreksi attendance manual.
- `attendance_corrections`: audit-ready correction log untuk attendance.
- `leave_requests`: izin/sakit, scoped by `client_id`.
- `payroll`: summary payroll per pegawai dan periode.
- `attendance_policies`: kebijakan attendance/payroll per client/site.

## Enterprise Contract & Billing

- `client_packages`: histori package active per client.
- `client_addons`: add-on enterprise per client.
- `client_contracts`: histori kontrak client, satu active record.
- `billing_configs`: konfigurasi billing active per client.

## RBAC, Scope, Audit

- `roles`: role enterprise canonical.
- `permissions`: permission granular.
- `role_permission_map`: relasi role-permission.
- `user_scopes`: scope user ke GLOBAL, CLIENT, SITE, atau SELF.
- `audit_logs`: audit event enterprise.
- `logs`: legacy operational log.
- `retention_policies`: aturan umur data.
- `login_attempts`: persistent login rate-limit log.

## Soft Delete Metadata

Tabel penting memiliki metadata:

- `deleted_at`
- `deleted_by`
- `delete_reason`

Tabel awal yang disiapkan: `employees`, `clients`, `sites`, `client_contracts`, `billing_configs`, `attendance_corrections`, `patrol_tours`, `patrol_operational_events`, dan `leave_requests`.
