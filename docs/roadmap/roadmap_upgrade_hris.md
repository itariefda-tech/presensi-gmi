# Roadmap Upgrade Presensi ke HRIS PRO

## Overview
Upgrade aplikasi presensi menjadi HRIS (Human Resource Information System) tanpa mengubah stack/framework yang ada. Fokus pada penambahan fitur HRIS bertahap dengan mempertahankan kode existing.

## Status Produk Saat Ini

Roadmap ini sekarang sudah melampaui bentuk awal `Presensi -> HRIS PRO`. Implementasi terkini sudah berkembang menjadi layer produk berikut:

- `HRIS Pro`
  - paket inti operasional
  - add-on lanjutan tidak otomatis aktif
- `HRIS Pro Plus`
  - tetap di basis Pro
  - add-on dapat dipilih custom satu per satu
- `HRIS Enterprise`
  - membuka seluruh add-on tier yang tersedia dari owner policy

Owner credential modal sekarang berfungsi sebagai pengendali induk untuk versi aplikasi dan add-on. Jadi layer versi tidak lagi sekadar label, tetapi sudah mempengaruhi UI, navigation, reporting, communication, promo guard tour, dan gating fitur di backend.

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
  - Manager Operational fallback
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
- [x] Buat folder: `/static/i18n/`
- [x] Buat file:
  - `id.json`
  - `en.json`

### Implementasi
- [x] Tambahkan attribute: `data-i18n`
- [x] Buat JS loader language
- [x] Buat fungsi: `applyLang()`

### UI Switch
- [x] Tambahkan tombol: ID / EN
- [x] Simpan di localStorage

---

## Phase 5: Multi Theme (dari 2 theme jadi 5 Theme)
- untuk semua ui kecuali ui dashboard client admin, jadi sementara biarkan saja jangan diubah atau disentuh.

### Target
UI premium + branding
Membangun sistem multi-theme yang:
  elegan & konsisten
  siap untuk branding client (white-label)
  scalable untuk SaaS / enterprise
  bukan sekadar variasi warna, tapi karakter visual berbeda

🎨 THEME YANG DIGUNAKAN (FINAL)
✅ Dengan:

 sage_calm → soft, natural, human-friendly
 silver_line → clean, corporate, minimal
 noir_warm → dark elegant, warm premium

🧩 THEME SYSTEM (WAJIB RAPUH → JADI SOLID)
1. Gunakan Attribute Theme
<html data-theme="sage_calm">
2. Struktur CSS Berbasis Token

Semua styling HARUS menggunakan variable:

:root{
  --bg;
  --panel;
  --text;
  --muted;
  --border;
  --accent;
}

Setiap theme override token ini.

3. Theme Switcher (Frontend)
 Tambahkan pilihan theme di UI hanya berada di halaman setting dengan menambahkan tab baru "Tema" pilihan hanya 3 (dropdown / segmented button), jangan ganggu togle tema light /dark, jadi biarkan yang lama tetap ada itu pertahankan sebagai  tema default. ketika user merasa bosen dia harus masuk ke setting tuju tab tema.

 Update data-theme secara realtime
 Simpan ke:
localStorage.setItem("theme", selectedTheme)
 Load saat aplikasi start

4. Default Behavior
Default theme: silver_line (paling netral untuk demo/client)
Fallback jika tidak ada: silver_line
🔌 INTEGRATION BACKEND (LEVEL UP)
5. User Preference

Tambahkan field:

theme_preference TEXT

Behavior:

Jika user login → gunakan theme user
Jika tidak ada → fallback ke localStorage
Jika kosong semua → gunakan default
6. Client-Based Theme (WHITE LABEL READY)

Tambahkan field:

client_theme TEXT

Behavior:

Jika client punya theme → override user
Jika tidak → gunakan user preference
⚙️ PRIORITY RESOLUTION (PENTING)

Urutan prioritas theme:

client_theme
user.theme_preference
localStorage
default (silver_line)
🧪 VALIDATION CHECKLIST
 Semua halaman konsisten (admin, employee, mobile)
 Tidak ada hardcoded color
 Semua pakai CSS variable
 Theme switch realtime tanpa reload
 Tidak ada konflik antar theme
🧨 CONSTRAINTS (JANGAN DILANGGAR)

JANGAN:

menambahkan theme random tanpa konsep
mencampur warna antar theme
menggunakan hardcoded warna di component
membuat styling berbeda-beda antar halaman
🏁 EXPECTED RESULT

Hasil akhir harus:

terasa seperti produk SaaS premium
bisa langsung dipakai untuk multiple client
mudah ditambah theme baru di masa depan
konsisten secara visual di semua halaman
🚀 OPTIONAL (NEXT LEVEL)
 Theme preview (live switch tanpa reload)
 Animasi transisi antar theme (halus)
 Theme config JSON (untuk dynamic branding)

### Status Implementasi Phase 5
- [x] Theme final dibatasi ke `sage_calm`, `silver_line`, dan `noir_warm` untuk pilihan Settings.
- [x] Default/fallback theme diset ke `silver_line`.
- [x] Token CSS theme ditambahkan untuk app, dashboard admin, dan mobile employee tanpa mengubah dashboard client admin.
- [x] Toggle light/dark lama tetap dipertahankan.
- [x] Tab Settings baru `Tema` dibuat dengan pilihan theme final.
- [x] Preferensi user disimpan ke `users.theme_preference`.
- [x] Field white-label client disiapkan di `clients.client_theme`.
- [x] Resolusi prioritas theme: `client_theme` > `user.theme_preference` > `localStorage` > `silver_line`.
- [x] Theme switch realtime tersambung via `data-theme` dan localStorage.
---

## Phase 6: Enterprise Core

### Target
Siap perusahaan 100-500 pegawai

### Multi Client & Branch
- [x] Tambahkan field:
  - `client_id`
  - `branch_id`
- [x] Filter semua data berdasarkan client

### Audit Log
- [x] Buat tabel `logs`
- [x] Simpan:
  - User
  - Action
  - Timestamp

### API Basic
- [x] Endpoint: `/api/v1/attendance`
- [x] Auth sederhana

---

## Phase 7: Enterprise Add-on (Killer Feature)

### Target
Pembeda utama di market security

### Patrol / Guard Tour
- [x] Buat tabel:
  - `patrol_points` (sebagai `patrol_checkpoints`)
  - `patrol_logs` (sebagai `patrol_scans`)
- [x] Flow: scan QR / GPS
- [x] Simpan:
  - Waktu
  - Lokasi
- [x] Admin Guard Tour Report Page:
  - Halaman dashboard `/dashboard/admin/guard-tour`
  - Filter: Site (wajib), Date Range (optional)
  - API endpoint: `/api/admin/guard_tour/report`
  - Export CSV support
  - Display: Guard Name, Site, Checkpoint, Check Time, Status, Notes

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
- [x] Attendance stabil
- [x] Leave berjalan
- [x] Approval center aktif
- [x] Payroll sederhana jalan
- [x] Tier system aktif

### HRIS ENTERPRISE READY (Red Check)
- [x] Multi client
- [x] Add-on system
- [x] Patrol aktif
- [x] Payroll advanced
- [ ] AI analysis basic

## Pencapaian Relevan Tambahan

- Reports sudah dibagi sesuai layer versi dan add-on.
- `HRIS Calendar Reports` hanya muncul jika fitur `Calendar` aktif.
- `Advanced Reporting` dan `Custom Report Builder` tidak tampil pada `HRIS Pro` murni.
- Promo paket untuk `Guard Tour` sudah memakai halaman brosur khusus agar pacing upgrade tidak tersebar ke banyak halaman.
- API access add-on sudah usable untuk integrasi attendance client.

---

## Notes
- Upgrade bertahap tanpa refactor besar
- Pertahankan stack/framework existing
- Fokus pada value tambah HRIS
- Siapkan untuk monetasi (tier system)
