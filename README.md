# HRIS GMI - Attendance & Leave System (Demo)

HRIS GMI adalah aplikasi HRIS ringan untuk presensi, izin, dan approval.
Fokus Phase 8: role access real (SQLite), HR settings, dan flow demo stabil.

## Run (Windows)

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

App: `http://localhost:5020/`

## Demo Accounts (Seed)

Password default untuk seed: `gmi@12345`

- hr_superadmin: `hr@gmi.com` / `hr123456`
- manager_operational: `manager@gmi.com` / `gmi@12345`
- supervisor: `supervisor@gmi.com` / `gmi@12345`
- admin_asistent: `asisten@gmi.com` / `gmi@12345`
- employee: `budi@gmi.com` / `gmi@12345`

## Roles (Final)

- hr_superadmin
- manager_operational
- supervisor
- admin_asistent
- employee

## HR Settings

HR superadmin bisa akses `Dashboard Admin -> Settings`:
- Users (add/edit/disable/reset password, assign sites)
- Sites (CRUD)
- Shifts (CRUD)

## Change Password

Semua role bisa ganti password dari dashboard masing-masing.
Jika `must_change_password = 1`, akan muncul banner pengingat.

## Demo vs Real (Storage)

- Users/Roles/Sites/Shifts: SQLite (real)
- Manual attendance requests: SQLite (real)
- Attendance checkin/checkout: demo in-memory
- Leave requests: demo in-memory

## Docs

- Audit notes: `docs/AUDIT_NOTES.md`
- Roadmap: `docs/roadmap.md`
