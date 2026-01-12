# Audit Entitas Client dan Relasinya (Merged)

Dokumen ini menggabungkan audit awal entitas Client dan versi pengembangan (client_entity2). Tujuannya: memetakan kondisi saat ini, gap terhadap standar outsourcing, dan rencana perbaikan bertahap yang realistis.

---

## 0) Ringkasan Eksekutif

**Kondisi saat ini:**
- [x] Entitas Client sudah ada (master dasar + 1 PIC).
- [x] Entitas Site sudah ada, relasi ke Client sudah memakai `client_id` (dengan `client_name` legacy untuk kompatibilitas).
- [x] Relasi pegawai & supervisor ke site sudah ada; assignment dinamis dan policy presensi per client/site sudah tersedia.

**Problem utama:**
- [x] Kontrak/SLA/billing belum tersedia sebagai modul/entitas.
- [x] `client_name` legacy masih berpotensi tidak sinkron saat rename.

**Arah solusi:**
- [x] Perkuat relasi dengan FK: `Client (1) -> (N) Site`.
- [x] Tambahkan jantung outsourcing:
  - [x] Assignment: Employee <-> Site dengan periode berlaku.
  - [x] AttendancePolicy: aturan presensi per client/site (inheritance).
- [ ] Tambah modul enterprise-ready secara bertahap:
  - [x] multi-PIC (client_contacts)
  - [ ] kontrak
  - [ ] SLA ringkas
  - [ ] billing

## 0.1) Status Implementasi (cek repo per 2026-01-08)

- [x] `sites.client_id` sudah ada + migrasi dari `client_name`; FK `sites.client_id -> clients.id` sudah diterapkan.
- [x] Tabel `assignments` sudah ada + CRUD + UI.
- [x] Tabel `attendance_policies` sudah ada + CRUD + dipakai saat presensi.
- [x] `employee_site` dan `supervisor_sites` masih ada (legacy); assignment aktif dipakai untuk presensi.
- [x] `clients` sudah punya `updated_at`, `legal_name`, `tax_id`, `status`, `contract_*` (UI belum expose kontrak).
- [x] `sites` sudah punya `client_id`, `address`, `updated_at`, `timezone`, `work_mode`.
- [x] `client_contacts` sudah ada + CRUD + UI (client profile).
- [ ] `client_contracts`, `client_billing` belum ada.
- [x] `shifts` sudah ada (schema + CRUD + UI) tetapi belum terhubung ke policy.

---

## 1) Terminologi Teknis

- "Data client" = entitas `Client` (master) + relasi terkait.
- "Koneksi client-site" = relasi via FK `sites.client_id`.
- "Pegawai ditugaskan" = Assignment (penempatan) dengan masa berlaku.
- "Aturan custom per client" = Attendance Policy Engine (policy scope & inheritance).
- "Relasi kuat" = FK (Foreign Key) + constraints untuk data integrity.

---

## 2) Snapshot Kondisi Saat Ini (Audit)

### 2.1 clients
Kolom:
- `id`, `name`, `legal_name`, `tax_id`, `status`
- `contract_no`, `contract_start`, `contract_end`
- `address`, `office_email`, `office_phone`
- `pic_name`, `pic_title`, `pic_phone`
- `is_active`, `notes`, `created_at`, `updated_at`

Kekurangan:
- Kontrak/SLA/billing belum ada sebagai modul khusus (baru kolom kontrak di clients)
- UI belum expose `tax_id`/`contract_*` (hanya `legal_name`)

### 2.2 sites
Kolom:
- `id`, `client_id`, `client_name` (legacy), `name`
- `address`
- `latitude`, `longitude`, `radius_meters`
- `notes`, `is_active`, `created_at`, `updated_at`

Kekurangan:
- Legacy `client_name` masih disimpan (perlu strategi cleanup bila tidak dibutuhkan).

### 2.3 Relasi yang terlihat
- Client -> Site: via `sites.client_id` (string legacy `client_name` masih disimpan)
- Supervisor -> Site: `supervisor_sites`
- Employee -> Site: `assignments` (utama), `employee_site` (legacy)
- Policy -> Client/Site: `attendance_policies`

Risiko teknis:
- Rename client membuat `sites.client_name` legacy tidak sinkron
- Unique index nama/legal name dicoba dibuat; jika data duplikat sudah ada, index gagal dibuat.

---

## 3) Sumber Data (Kode)

- Skema tabel client: `app.py:2955` (CREATE TABLE `clients`).
- Skema tabel client_contacts: `app.py:2979`.
- Skema tabel site: `app.py:3026`.
- Skema tabel assignments: `app.py:3078`.
- Skema tabel attendance_policies: `app.py:3093`.
- Operasi CRUD client: `app.py:3838`, `app.py:3890`, `app.py:3945`.
- CRUD site: `app.py:4605`, `app.py:4650`, `app.py:4696`.
- CRUD assignments: `app.py:3955`, `app.py:4007`, `app.py:4118`.
- CRUD policies: `app.py:4138`, `app.py:4215`, `app.py:4297`.
- CRUD client_contacts: `app.py:3708`, `app.py:3743`, `app.py:3755`.
- UI admin client: `templates/dashboard/admin_clients.html`.
- UI admin assignments: `templates/dashboard/admin_assignments.html`.
- UI admin policies: `templates/dashboard/admin_policies.html`.
- UI client profile (tabs + contacts): `templates/dashboard/admin_client_profile.html`.

---

## 4) Target Data Model (Standar Outsourcing)

### 4.1 ERD Ringkas (Target)
- Client (1) -> (N) Site
- Site (N) <-> (N) Employee via Assignment
- AttendancePolicy berlaku:
  - level Client (default)
  - level Site (override)
  - (opsional) level Employee (exception)
- Shift dan OvertimeRule terhubung ke AttendancePolicy
- ClientContacts menyimpan multi-PIC
- Contracts / SLA / Billing bertahap (minimal fields dulu)

---

## 5) Desain Entitas Inti (Core Tables)

### 5.1 clients (upgrade minimal enterprise)
Tambahkan kolom:
- `legal_name` TEXT NULL
- `tax_id` TEXT NULL (NPWP)
- `status` TEXT NOT NULL DEFAULT 'ACTIVE' (ACTIVE/INACTIVE/SUSPENDED)
- `contract_no` TEXT NULL
- `contract_start` TEXT NULL (ISO date)
- `contract_end` TEXT NULL (ISO date)
- `updated_at` TEXT NULL

Constraints disarankan:
- `UNIQUE(name)` atau `UNIQUE(legal_name)` (pilih yang paling stabil di bisnis)

Catatan:
- `name` bisa jadi brand/display name.
- `legal_name` untuk urusan kontrak/NPWP.

### 5.2 sites (wajib pindah dari string ke FK)
Perubahan inti:
- Tambahkan `client_id` INTEGER NOT NULL
- Jadikan `client_id` sebagai FK ke `clients.id`

Tambahan opsional:
- `address` TEXT NULL
- `timezone` TEXT NULL (default 'Asia/Jakarta')
- `work_mode` TEXT NULL (onsite/hybrid)
- `updated_at` TEXT NULL

### 5.3 assignments (jantung outsourcing)
Tujuan:
- Menjawab "pegawai A kerja untuk client B di site C pada periode tertentu"

Kolom minimal:
- `id` INTEGER PK
- `employee_user_id` INTEGER NOT NULL
- `site_id` INTEGER NOT NULL
- `job_title` TEXT NULL
- `start_date` TEXT NOT NULL
- `end_date` TEXT NULL
- `status` TEXT NOT NULL DEFAULT 'ACTIVE' (ACTIVE/ENDED)
- `created_at` TEXT NOT NULL
- `updated_at` TEXT NULL

Constraints disarankan:
- Index: `(employee_user_id, status)`, `(site_id, status)`
- Rule aplikasi: 1 assignment ACTIVE per employee (atau multi-site jika dibutuhkan)

Dampak UI:
- Dashboard pegawai menampilkan Client + Site aktif dari assignment ACTIVE
- Validasi presensi menggunakan site dari assignment aktif

### 5.4 attendance_policies (policy engine)
Target:
- Tiap client punya aturan presensi berbeda; site bisa override.

Kolom minimal:
- `id` INTEGER PK
- `scope_type` TEXT NOT NULL ('CLIENT' / 'SITE')
- `client_id` INTEGER NULL
- `site_id` INTEGER NULL
- `effective_from` TEXT NOT NULL
- `effective_to` TEXT NULL

Aturan kerja:
- `work_duration_minutes` INTEGER NULL
- `grace_minutes` INTEGER NULL
- `late_threshold_minutes` INTEGER NULL
- `allow_gps` INTEGER NOT NULL DEFAULT 1
- `require_selfie` INTEGER NOT NULL DEFAULT 1
- `allow_qr` INTEGER NOT NULL DEFAULT 0
- `auto_checkout` INTEGER NOT NULL DEFAULT 0
- `cutoff_time` TEXT NULL

Constraints disarankan:
- Hanya salah satu dari `(client_id, site_id)` terisi sesuai `scope_type`
- Index: `(scope_type, client_id)`, `(scope_type, site_id)`

Policy Inheritance:
1) Cari policy SITE aktif (override)
2) Jika tidak ada, pakai policy CLIENT aktif (default)
3) Jika tidak ada, pakai default sistem

### 5.5 shifts & overtime_rules (tahap berikutnya)
- `shifts`: nama shift, jam masuk/keluar, toleransi (sudah ada schema + CRUD + UI, belum terhubung ke policy)
- `overtime_rules`: aturan lembur (min minutes, rounding, approval)

Relasi:
- Policy <-> Shift (many-to-many) atau policy punya `default_shift_id`

---

## 6) Entitas Pendukung (Enterprise-Ready, Bertahap)

### 6.1 client_contacts (multi-PIC)
Kolom minimal:
- `id` PK
- `client_id` FK
- `type` TEXT NOT NULL ('OPERATIONAL','BILLING','HR','OTHER')
- `name` TEXT NOT NULL
- `title` TEXT NULL
- `email` TEXT NULL
- `phone` TEXT NULL
- `is_primary` INTEGER NOT NULL DEFAULT 0
- `notes` TEXT NULL
- `is_active` INTEGER NOT NULL DEFAULT 1

### 6.2 contracts / SLA (minimal)
`client_contracts` (opsional):
- `contract_no`, `start_date`, `end_date`, `notice_period_days`, `scope_summary`, `sla_summary`

### 6.3 billing (opsional fase 2-3)
`client_billing` (opsional):
- `billing_type` (PER_HEAD/PER_SITE/PER_SHIFT)
- `rate`
- `tax_percent`
- `payment_terms_days`
- `bank_account`
- `invoice_email`

---

## 7) Migrasi Aman (Non-Blocking Plan)

### Phase A - Perbaiki relasi Client -> Site (wajib)
- [x] Tambahkan `client_id` ke `sites`
- [x] Isi `client_id` berdasarkan mapping `sites.client_name` -> `clients.name`
- [x] Hentikan penggunaan `client_name` untuk relasi (boleh disimpan sementara)
- [x] Tambahkan constraint FK (jika memungkinkan)

### Phase B - Tambah Assignment (wajib untuk outsourcing)
- [x] Buat tabel `assignments`
- [x] Migrasikan relasi lama `employee_site` menjadi assignment ACTIVE
- [x] Update dashboard pegawai untuk menampilkan client + site aktif

### Phase C - Policy minimal per client/site
- [x] Buat tabel `attendance_policies`
- [ ] Set default policy per client (data belum diisi)
- [x] Tambah override policy per site
- [x] Ubah validasi presensi server untuk mengambil aturan dari policy

---

## 8) Dampak UI/UX (Terasa Profesional)

### Admin - Client Profile Tabs (recommended)
- [x] Overview
- [x] Sites
- [x] Assignments
- [x] Policies
- [ ] Contracts
- [x] Contacts (PIC)

### Employee Dashboard (impact cepat)
- [x] Tampilkan Client aktif
- [x] Tampilkan Site aktif
- [x] Validasi presensi berdasarkan assignment dan policy

---

## 9) Checklist Implementasi

Wajib (integrity + outsourcing):
- [x] `sites.client_id` FK
- [x] `assignments` table
- [x] dashboard pegawai tampilkan client + site dari assignment

Canggih tapi ringan:
- [x] `attendance_policies` + inheritance (client default -> site override) (fitur ada; data perlu diisi)
- [x] `client_contacts` multi-PIC

Komersial (tahap berikutnya):
- [ ] contracts + SLA ringkas (belum ada)
- [ ] billing schema (belum ada)

---

## 10) Catatan Penting

- [ ] Jangan mengandalkan string untuk relasi (nama bisa berubah).
- [ ] Pastikan ada `updated_at` untuk audit perubahan.
- [ ] Minimal constraint:
  - [ ] `clients.name` unik (atau `legal_name` unik)
  - [ ] assignment ACTIVE per employee dibatasi (di level app atau constraint)

---

## 11) Status Keputusan

Rekomendasi ini non-blocking untuk demo, tapi:
- [x] FK `client_id` di `sites` + assignment adalah pondasi penting agar sistem naik kelas.
- [x] Policy engine adalah pembeda utama agar HRIS terlihat seperti platform.

## 12) Catatan Mock/Orphan/Kontradiksi

- [x] UI `admin_assignments.html` dan `admin_policies.html` sudah terhubung ke backend.
- [x] Legacy `client_name` dan `employee_site` masih ada sebagai kompatibilitas (potensi orphan jika tidak dimigrasi penuh).
- [ ] Kontrak/billing belum ada (UI dan backend).
