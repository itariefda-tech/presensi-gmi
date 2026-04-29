==================================================
PHASE 16 - HARDENING & SCALE (POST ENTERPRISE)
==================================================

Goal:
- Sistem stabil untuk multi-client enterprise
- Minim demo logic
- Data aman, cepat, dan audit-ready

Scope:
- Security hardening
- RBAC granular
- Soft delete
- Retention policy
- Performance indexing
- Migration readiness
- Final technical documentation

Dependency:
- Phase 15 selesai minimal:
  - client package
  - client addon
  - client contract
  - billing config
  - client_id mapping

  1. Database Hardening
Objective

Memastikan semua data penting sudah persist ke database, bukan memory/demo state.

Checklist :
- [x] Attendance sudah ke DB
- [x] Leave sudah ke DB
- [ ] Semua modul utama tidak pakai in-memory demo
- [ ] Standardisasi created_at / updated_at
- [ ] Tambah deleted_at untuk soft delete
- [ ] Tambah created_by / updated_by jika perlu audit

Tabel yang perlu diperiksa
employees
attendance
leave_requests
clients
sites
shifts
payroll_policies
client_contracts
client_billing
client_packages
client_addons
patrol_reports

2. Permission Matrix Granular
Objective

Role tidak hanya global, tapi juga punya scope per client / site.

Role minimum
OWNER
SUPERADMIN
CLIENT_ADMIN
HR_ADMIN
FINANCE
SUPERVISOR
EMPLOYEE
AUDITOR

Permission contohattendance.view
attendance.export
attendance.approve

payroll.view
payroll.process
payroll.export

billing.view
billing.config.update

contract.view
contract.manage

patrol.view
patrol.create
patrol.review

employee.view
employee.manage

site.view
site.manage

Scope : 
GLOBAL
CLIENT
SITE
SELF

Contoh: 
OWNER        → GLOBAL
CLIENT_ADMIN → CLIENT
SUPERVISOR   → SITE
EMPLOYEE     → SELF

3. RBAC Table Mapping

Tambahkan tabel:
CREATE TABLE IF NOT EXISTS roles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  role_key TEXT UNIQUE NOT NULL,
  role_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS permissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  permission_key TEXT UNIQUE NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  role_id INTEGER NOT NULL,
  permission_id INTEGER NOT NULL,
  UNIQUE(role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS user_scopes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  client_id INTEGER,
  site_id INTEGER,
  scope_type TEXT NOT NULL DEFAULT 'SELF'
);

4. Soft Delete
Objective

Data tidak langsung hilang permanen.

Tambahkan kolom:

deleted_at TEXT;
deleted_by INTEGER;
delete_reason TEXT;

Berlaku untuk:
employees
clients
sites
contracts
billing_configs
attendance_corrections
patrol_reports
leave_requests

Rule

DELETE biasa diganti menjadi UPDATE deleted_at
Data deleted tidak tampil di UI default
Owner/Auditor bisa lihat deleted data

5. Retention Policy
Objective

Mengatur umur data agar aman secara legal dan performa tetap sehat.

Contoh policy

attendance records     → simpan 5 tahun
payroll summary        → simpan 5 tahun
patrol reports         → simpan 3 tahun
audit logs             → simpan 5 tahun
temporary uploads      → hapus 30-90 hari

Tabel baru 

CREATE TABLE IF NOT EXISTS retention_policies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data_type TEXT NOT NULL,
  retention_days INTEGER NOT NULL,
  action TEXT NOT NULL DEFAULT 'ARCHIVE',
  is_active INTEGER NOT NULL DEFAULT 1
);

6. Audit Log

Ini sangat penting untuk enterprise.

Objective

Mencatat siapa melakukan apa.

CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_user_id INTEGER,
  client_id INTEGER,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id INTEGER,
  before_json TEXT,
  after_json TEXT,
  ip_address TEXT,
  user_agent TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

Contoh action
CREATE_EMPLOYEE
UPDATE_ATTENDANCE
DELETE_SITE
ENABLE_BILLING_ADDON
UPDATE_PAYROLL_POLICY
APPROVE_LEAVE

7. Indexing & Performance
Objective

Dashboard tetap cepat walaupun data besar.

Index wajib
CREATE INDEX IF NOT EXISTS idx_attendance_client_date
ON attendance(client_id, attendance_date);

CREATE INDEX IF NOT EXISTS idx_attendance_employee_date
ON attendance(employee_id, attendance_date);

CREATE INDEX IF NOT EXISTS idx_employees_client_site
ON employees(client_id, site_id);

CREATE INDEX IF NOT EXISTS idx_leave_client_status
ON leave_requests(client_id, status);

CREATE INDEX IF NOT EXISTS idx_audit_client_created
ON audit_logs(client_id, created_at);

CREATE INDEX IF NOT EXISTS idx_contract_client_active
ON client_contracts(client_id, is_active);

CREATE INDEX IF NOT EXISTS idx_billing_client_active
ON client_billing(client_id, is_active);

8. MySQL Readiness
Objective

Saat infra siap, SQLite bisa dipindah ke MySQL tanpa rewrite besar.

Checklist

- [ ] Hindari SQL yang terlalu SQLite-specific
- [ ] Buat database adapter/helper
- [ ] Semua query lewat get_db()
- [ ] Tipe tanggal konsisten ISO string
- [ ] Hindari hardcoded file database
- [ ] Buat migration notes SQLite → MySQL

9. Security Hardening
Checklist

- [ ] Semua route wajib login
- [ ] Semua route admin wajib role check
- [ ] Semua data query wajib filter client_id
- [ ] CSRF protection untuk form POST
- [ ] Password hashing aman
- [ ] Session timeout
- [ ] Rate limit login
- [ ] Hide debug mode di production
- [ ] Validasi input server-side

10. Final Documentation
File docs yang disarankan

docs/
├─ ERD_ENTERPRISE.md
├─ API_SPEC_ENTERPRISE.md
├─ RBAC_MATRIX.md
├─ MIGRATION_SQLITE_TO_MYSQL.md
├─ AUDIT_LOG_POLICY.md
├─ RETENTION_POLICY.md
└─ DEPLOYMENT_CHECKLIST.md

Urutan Implementasi Paling Aman
STEP 1
Audit ulang semua demo/in-memory logic

STEP 2
Tambahkan client_id consistency di modul utama

STEP 3
Tambahkan RBAC granular + user scope

STEP 4
Tambahkan soft delete

STEP 5
Tambahkan audit log

STEP 6
Tambahkan retention policy

STEP 7
Tambahkan indexing

STEP 8
Rapikan security route guard

STEP 9
Siapkan MySQL readiness

STEP 10
Final docs + migration notes

Outcome Phase 16

✔ Sistem siap multi-client enterprise
✔ Data aman dan bisa diaudit
✔ Role lebih rapi dan granular
✔ Dashboard tetap cepat
✔ Siap migrasi ke MySQL
✔ Siap masuk tahap production / komersialisasi