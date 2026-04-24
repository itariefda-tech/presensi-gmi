# Roadmap Upgrade Presensi ke HRIS PRO

## Overview
Upgrade aplikasi presensi menjadi HRIS (Human Resource Information System) tanpa mengubah stack/framework yang ada. Fokus pada penambahan fitur HRIS bertahap dengan mempertahankan kode existing.

---

## Phase 1: Foundation (Presensi -> HRIS PRO)

### Target
Sistem "terasa HRIS", bukan sekedar presensi

### Branding & Struktur
- [x] Ubah judul UI menjadi "HRIS PRO - Workforce Control"
- [x] Tambah menu: Dashboard / Attendance / Leave / Approval Center
- [x] Ubah istilah:
  - "Presensi" -> "Attendance"
  - "Manual Presensi" -> "Manual Attendance Request"

### Leave System (WAJIB)
- [x] Buat tabel `leave_requests`
- [x] Buat endpoint:
  - `POST /api/leave/create`
  - `GET /api/leave/my`
- [x] Tambah field:
  - `type` (izin/sakit)
  - `date_from`
  - `date_to`
  - `reason`
- [x] Implement approval:
  - Supervisor approve
  - Koordinator fallback
- [x] Tambahkan status: pending / approved / rejected

### Approval Center
- [x] Gabungkan:
  - Manual attendance
  - Leave request
- [x] Buat endpoint: `GET /api/approval/pending`
- [x] Buat UI 1 halaman dengan tab:
  - Tab Attendance
  - Tab Leave
- [x] Tambahkan action: approve / reject

---

## Phase 2: HRIS PRO (Siap Dijual)

### Target
Bisa closing client pertama

### Tier System
- [x] Tambahkan field `tier` di tabel user
- [x] Default = basic
- [x] Buat helper:
  - `is_pro(user)`
  - `is_enterprise(user)`

### Feature Lock (Upsell)
- [x] Lock QR attendance: hanya PRO
- [x] Lock manual attendance: hanya PRO
- [x] Tambahkan pesan: "Upgrade ke HRIS PRO"

### Payroll Sederhana
- [x] Buat tabel `payroll`
- [x] Tambahkan field:
  - `salary_base`
  - `potongan_telat`
  - `potongan_absen`
- [x] Hitung:
  - Hadir
  - Telat
  - Absen
  - Leave
- [x] API:
  - `POST /api/payroll/generate`
  - `GET /api/payroll/list`
- [x] UI: Generate + Listkan total gaji

### Reporting Basic
- [x] Rekap attendance harian
- [x] Rekap telat
- [x] Rekap absen
- [x] Export sederhana (optional CSV)

---

## Phase 3: Add-on System (Jalur Enterprise)

### Target
Produk modular & scalable

### Struktur Add-on
- [x] Tambahkan field `addons` di tabel client
- [x] Format JSON: `["patrol","payroll_plus","ai"]`

### Helper Add-on
- [x] Buat fungsi: `has_addon(client, feature)`

### Integrasi Add-on
- [x] Lock fitur berdasarkan addon:
  - Patrol
  - Reporting advanced
  - API access

---

## Phase 4: Dual Language (ID + EN)

### Target
Profesional & tidak membingungkan

### Setup Bahasa
- [ ] Buat folder: `/static/i18n/`
- [ ] Buat file:
  - `id.json`
  - `en.json`

### Implementasi
- [ ] Tambahkan attribute: `data-i18n`
- [ ] Buat JS loader language
- [ ] Buat fungsi: `applyLang()`

### UI Switch
- [ ] Tambahkan tombol: ID / EN
- [ ] Simpan di localStorage

---

## Phase 5: Multi Theme (5 Theme)

### Target
UI premium + branding

### Tambah Theme Baru
- [ ] Ocean
- [ ] Sunset
- [ ] Forest

### Theme System
- [ ] Gunakan `data-theme`
- [ ] Simpan di localStorage

### Advanced
- [ ] Tambahkan field `theme_preference` di user
- [ ] Tambahkan theme per client

---

## Phase 6: Enterprise Core

### Target
Siap perusahaan 100-500 pegawai

### Multi Client & Branch
- [ ] Tambahkan field:
  - `client_id`
  - `branch_id`
- [ ] Filter semua data berdasarkan client

### Audit Log
- [ ] Buat tabel `logs`
- [ ] Simpan:
  - User
  - Action
  - Timestamp

### API Basic
- [ ] Endpoint: `/api/v1/attendance`
- [ ] Auth sederhana

---

## Phase 7: Enterprise Add-on (Killer Feature)

### Target
Pembeda utama di market security

### Patrol / Guard Tour
- [ ] Buat tabel:
  - `patrol_points`
  - `patrol_logs`
- [ ] Flow: scan QR / GPS
- [ ] Simpan:
  - Waktu
  - Lokasi

### Dana Talangan
- [ ] Buat tabel `loan`
- [ ] Field:
  - Jumlah
  - Cicilan
- [ ] Integrasi: potong payroll

### AI Analysis (Basic Rule-Based)
- [ ] Hitung:
  - Pegawai sering telat
  - Pegawai sering absen
  - Ranking disiplin

---

## Final Checklist

### HRIS PRO READY (Green Check)
- [ ] Attendance stabil
- [ ] Leave berjalan
- [ ] Approval center aktif
- [ ] Payroll sederhana jalan
- [ ] Tier system aktif

### HRIS ENTERPRISE READY (Red Check)
- [ ] Multi client
- [x] Add-on system
- [ ] Patrol aktif
- [ ] Payroll advanced
- [ ] AI analysis basic

---

## Notes
- Upgrade bertahap tanpa refactor besar
- Pertahankan stack/framework existing
- Fokus pada value tambah HRIS
- Siapkan untuk monetasi (tier system)
