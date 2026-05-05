# HRIS GMI - Attendance & Leave System

HRIS GMI adalah aplikasi HRIS ringan untuk presensi, izin, dan approval.
Fokus Phase 8: role access real (SQLite), HR settings, dan flow aplikasi stabil.

## Karakter Aplikasi

HRIS GMI bukan landing page atau demo HR biasa, tetapi aplikasi operasional harian yang dipakai untuk mengelola tenaga kerja outsource secara langsung. Karakter utamanya:

- **Operasional dulu, kosmetik belakangan**  
  Struktur halaman, filter, dan alur fitur diarahkan untuk pekerjaan admin, HR, supervisor, dan employee yang berulang setiap hari.

- **Berbasis site dan assignment nyata**  
  Sistem dibangun dengan konsep `client -> site -> assignment -> employee`, jadi logika presensi, payroll, reporting, dan komunikasi mengikuti struktur kerja lapangan.

- **Modular dengan layer versi aplikasi**  
  Aplikasi sekarang punya layer `HRIS Pro`, `HRIS Pro Plus`, dan `HRIS Enterprise`, dengan owner toggle sebagai pengendali induk untuk add-on dan perilaku fitur.

- **Satu produk, banyak mode kerja**  
  Employee dashboard, admin dashboard, client scope, attendance, reporting, payroll, communication, patrol, hingga API access berada dalam satu codebase dan satu model data.

- **Siap tumbuh bertahap**  
  Fitur tidak dipukul rata. Beberapa area hanya hidup bila paket atau add-on aktif, sehingga aplikasi bisa dipakai dari core workflow sampai enterprise workflow yang lebih kompleks.

## Pencapaian Saat Ini

Sampai titik ini, aplikasi sudah berkembang cukup jauh dari sistem presensi dasar. Ringkasnya:

- **Core HRIS stabil**
  - login, signup, reset password
  - attendance check-in / check-out
  - leave, approval, manual attendance
  - role & permission berbasis SQLite

- **Struktur organisasi dan operasional sudah matang**
  - client, site, assignment, policy, shift
  - flow berbasis site sebagai unit kerja utama
  - filter yang mengkerucut di beberapa dashboard penting

- **Layer versi dan add-on owner sudah hidup**
  - `HRIS Pro`
  - `HRIS Pro Plus`
  - `HRIS Enterprise`
  - owner credential modal menjadi sumber perintah utama untuk add-on dan layer versi

- **Reporting sudah berkembang**
  - Reports Dashboard
  - HRIS Calendar Reports
  - Advanced Reporting
  - Custom Report Builder
  - gating laporan kini mengikuti paket / add-on secara lebih konsisten

- **Payroll sudah berjalan**
  - generate payroll
  - detail payroll
  - payroll adjustment
  - filter payroll sudah dirapikan agar mengikuti policy site, bukan duplikasi aturan manual

- **Operational Communication sudah tersedia**
  - chat room operasional
  - announcement
  - incident reporting
  - thread discussion
  - owner policy dan tier communication

- **API Access add-on sudah usable**
  - owner toggle
  - client activation
  - token generate / revoke
  - token hashing
  - scoped attendance API
  - usage log dan hardening dasar

- **Guard Tour dan promo paket sudah diarahkan**
  - akses Guard Tour mengikuti layer versi dan add-on
  - halaman promo khusus untuk paket / add-on Guard Tour sudah tersedia

- **Dokumentasi dan test bertambah**
  - roadmap dan dokumen fitur penting sudah mulai dipisah
  - regression test untuk API access, billing/contract, theme/owner settings, dan operational communication sudah ada

Secara keseluruhan, repo ini sekarang sudah berada di fase **HRIS operasional modular**: bukan lagi presensi sederhana, tetapi platform kerja yang mulai punya versi produk, add-on, aturan akses, dan pengalaman dashboard yang lebih spesifik per fungsi.

## Run (Windows)

1. **Dev standar**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   set FLASK_SECRET=isi-secret-kuat-minimal-32-karakter
   set PRESENSI_DB_PATH=presensi.db
   python app.py
   ```
   `FLASK_SECRET` wajib. Aplikasi akan gagal start jika secret kosong.

2. **Alternate (env Windows)**
   ```powershell
   set FLASK_SECRET=isi-secret-kuat-minimal-32-karakter
   set PRESENSI_DB_PATH=C:\path\ke\presensi.db
   set ENABLE_SEED_DATA=1
   set SEED_USERS_JSON=[{"email":"admin@example.com","name":"HR Superadmin","role":"hr_superadmin","password":"ganti-password-kuat"}]
   python app.py
   ```
   Gunakan cara ini kalau Anda sudah punya virtual environment aktif dan hanya ingin mengganti path DB atau override seed.

3. **One-command helper**
   ```powershell
   .\scripts\run_dev_windows.ps1
   ```
   Script ini membuat `.venv` bila belum ada, set `FLASK_SECRET` dev-session dan `PRESENSI_DB_PATH`, lalu menjalankan `python app.py`. Seed user tidak aktif secara default. Jika butuh seed lokal, pakai `-EnableSeedData -SeedUsersJson '...'`.

App: `http://localhost:5020/`

## Password Reset Delivery

Endpoint lupa password aktif jika salah satu delivery dikonfigurasi:

- Email SMTP: `RESET_SMTP_HOST`, `RESET_SMTP_PORT`, `RESET_SMTP_USER`, `RESET_SMTP_PASSWORD`, `RESET_SMTP_FROM`
- WhatsApp webhook: `RESET_WHATSAPP_WEBHOOK_URL`
- Public link base: `APP_PUBLIC_URL`

Tanpa delivery, tombol reset password akan nonaktif. Untuk debug lokal saja, `SHOW_RESET_TOKEN=1` mengembalikan token dan link reset di response API.

## Run (Docker)

1. Build the container image from the repo root:

   ```bash
   docker build -t presensi-app .
   ```

2. Start the container and expose the application port:

   ```bash
   docker run -d --name presensi-app -p 5050:5050 presensi-app
   ```

## Demo Accounts (Seed)

Seed data nonaktif secara default. Untuk mengaktifkan secara eksplisit:

- `ENABLE_SEED_DATA=1`
- `SEED_USERS_JSON` wajib berisi array user (email, name, role, password)
- Jangan gunakan credential default/publik untuk environment bersama atau production.

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

## Storage (Ringkas)

- Users/Roles/Sites/Shifts: SQLite (real)
- Manual attendance requests: SQLite (real)
- Attendance checkin/checkout: SQLite (real)
- Leave requests: SQLite (real)

+--------------------+          1        N          +--------------------+
|       CLIENTS      |------------------------------|        SITES       |
+--------------------+                              +--------------------+
| id (PK)            |                              | id (PK)            |
| name               |                              | client_id (FK)     |
| legal_name         |                              | name               |
| tax_id (NPWP)      |                              | address            |
| status             |                              | latitude           |
| contract_no        |                              | longitude          |
| contract_start     |                              | radius_meters      |
| contract_end       |                              | is_active          |
| notes              |                              | notes              |
| created_at         |                              | created_at         |
| updated_at         |                              | updated_at         |
+--------------------+                              +--------------------+

                           N        N
                           |        |
                           |        |
                           v        v
                    +----------------------+
                    |      ASSIGNMENTS     |
                    +----------------------+
                    | id (PK)              |
                    | employee_user_id (FK)|
                    | site_id (FK)         |
                    | job_title            |
                    | start_date           |
                    | end_date             |
                    | status (ACTIVE/ENDED)|
                    | created_at           |
                    | updated_at           |
                    +----------------------+
                           ^
                           |
                           | 1
                           |
+--------------------+     |     (1 employee can have 1 ACTIVE assignment by rule)
|       USERS         |----- 
+--------------------+
| id (PK)            |
| email              |
| role               |
| name               |
| ...                |
+--------------------+


POLICY (Inheritance: SITE override -> CLIENT default -> SYSTEM fallback)

+-------------------------+
|    ATTENDANCE_POLICIES  |
+-------------------------+
| id (PK)                 |
| scope_type (CLIENT/SITE)|
| client_id (FK, nullable)|
| site_id (FK, nullable)  |
| effective_from          |
| effective_to            |
| work_duration_minutes   |
| grace_minutes           |
| late_threshold_minutes  |
| allow_gps (0/1)         |
| require_selfie (0/1)    |
| allow_qr (0/1)          |
| auto_checkout (0/1)     |
| cutoff_time             |
| created_at              |
| updated_at              |
+-------------------------+
        ^                         ^
        |                         |
        | (default)               | (override)
        |                         |
        | 1                       | 1
+--------------------+          +--------------------+
|       CLIENTS      |          |        SITES       |
+--------------------+          +--------------------+


CLIENT CONTACTS (multi-PIC)
+------------------------+
|    CLIENT_CONTACTS     |
+------------------------+
| id (PK)                |
| client_id (FK)         |
| type (OP/BILL/HR/OTHER)|
| name                   |
| title                  |
| email                  |
| phone                  |
| is_primary (0/1)       |
| notes                  |
| is_active (0/1)        |
| created_at             |
| updated_at             |
+------------------------+
            ^
            | N
            | 
            | 1
+--------------------+
|      CLIENTS       |
+--------------------+


CONTRACTS (minimal enterprise)
+------------------------+
|    CLIENT_CONTRACTS    |
+------------------------+
| id (PK)                |
| client_id (FK)         |
| contract_no            |
| start_date             |
| end_date               |
| notice_period_days     |
| scope_summary          |
| sla_summary            |
| created_at             |
| updated_at             |
+------------------------+
            ^
            | N
            |
            | 1
+--------------------+
|      CLIENTS       |
+--------------------+


BILLING (optional)
+------------------------+
|     CLIENT_BILLING     |
+------------------------+
| id (PK)                |
| client_id (FK)         |
| billing_type           |
| rate                   |
| tax_percent            |
| payment_terms_days     |
| invoice_email          |
| bank_account           |
| created_at             |
| updated_at             |
+------------------------+
            ^
            | 0..1 (or N if multi plan)
            |
            | 1
+--------------------+
|      CLIENTS       |
+--------------------+


SHIFT + OVERTIME (optional, tied to policy)
+-------------------+        N     N        +-------------------------+
|       SHIFTS      |-----------------------|   POLICY_SHIFTS (link)  |
+-------------------+                       +-------------------------+
| id (PK)           |                       | policy_id (FK)          |
| name              |                       | shift_id (FK)           |
| start_time        |                       +-------------------------+
| end_time          |
| grace_minutes     |
| notes             |
+-------------------+

+-------------------+        1     N        +-------------------------+
|   OVERTIME_RULES  |-----------------------|   ATTENDANCE_POLICIES   |
+-------------------+                       +-------------------------+
| id (PK)           |                       | id (PK)                 |
| policy_id (FK)    |                       | ...                     |
| min_minutes       |                       +-------------------------+
| rounding_minutes  |
| require_approval  |
| notes             |
+-------------------+

## Domain Model

Sistem ini menggunakan konsep **Site** sebagai unit kerja operasional utama.

Penjelasan lengkap dapat dilihat di:
👉 docs/domain-model.md

## Docs

- Audit notes: `docs/AUDIT_NOTES.md`
- Roadmap: `docs/roadmap.md`
- focus detail : `register_issue.md` dan `client_entity.md`
- edukasi : `glosarium` dan `template_investigasi`

## Android (Capacitor)

- Wrapper project lives in `mobile-capacitor/`; read `mobile-capacitor/README_MOBILE.md` for full setup.
- Mode A keeps the app hosted at `https://absensi.gajiku.online` (or `http://127.0.0.1:5020` for dev) and runs inside Capacitor’s WebView so the existing UI is untouched.
- Guides include runtime permission handling (camera/QR, location, file upload), building the Android APK, and troubleshooting mixed content/session issues.

## Panduan Pull

Jika belum ada repo di perangkat lain:

```bash
git clone https://github.com/itariefda-tech/presensi-gmi.git
cd presensi-gmi
```

Jika repo sudah ada:

```bash
cd presensi-gmi
git pull origin main
```


jka npn run dev tidak bisa:

$env:Path = "C:\Windows\System32;C:\Windows;C:\Windows\System32\Wbem;" + $env:Path
npm run dev

set permanent :
setx PATH "C:\Windows\System32;C:\Windows;C:\Windows\System32\Wbem;%PATH%"

