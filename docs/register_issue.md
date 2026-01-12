# Investigasi Alur Pendaftaran

## 1. Tata Cara Pendaftaran

1. Pengguna membuka halaman login/daftar di `templates/index.html`, lalu memilih tab Daftar.
2. Pengguna mengisi: kode pendaftaran/undangan, email, password, ulangi password, dan selfie.
3. Frontend (`static/js/app.js`) mengirim `multipart/form-data` ke endpoint `POST /api/auth/signup`.
4. Backend (`app.py`) melakukan validasi:
   - Kode pendaftaran/undangan wajib.
   - Email valid.
   - Password minimal 6 karakter dan harus sama.
   - Selfie wajib.
5. Backend memvalidasi kode pendaftaran/undangan:
   - Jika kode `SUDAHBYADMIN`, maka email harus sudah ada di tabel `employees` (aktif/nonaktif).
   - Jika bukan, harus mengikuti format kode (contoh: `2501GMI-00103`).
6. Backend mengecek email belum terdaftar di tabel `users`.
7. Backend memulai transaksi DB; untuk kode normal mengurangi kuota kode pendaftaran/undangan.
8. Backend membuat akun baru (selfie_path kosong), menyimpan selfie, memperbarui selfie_path, dan (untuk `SUDAHBYADMIN`) mengaktifkan data master pegawai.


## 1A. Trace Eksekusi Signup (Submit -> DB)

1. Form signup di `templates/index.html:124` memakai `id="form-signup"` dan field `invite_code`, `email`, `password`, `password2`, `selfie` (`templates/index.html:136`, `templates/index.html:145`, `templates/index.html:163`, `templates/index.html:173`).
2. `static/js/app.js:183` mengikat submit via `bindSignupMultipart()` dan melakukan validasi frontend (toast): invite code wajib (`static/js/app.js:198`), email wajib (`static/js/app.js:202`), password minimal 6 karakter (`static/js/app.js:206`), password harus sama (`static/js/app.js:210`), selfie wajib (`static/js/app.js:214`).
3. Frontend membuat `FormData` dan mengirim `POST /api/auth/signup` (multipart/form-data) (`static/js/app.js:218`, `static/js/app.js:228`).
4. Backend `app.py:38` menerima `request.form` + `request.files` di `signup()` lalu validasi server:
   - Invite code wajib (`app.py:47`).
   - Email format valid (`_looks_like_email`) (`app.py:49`).
   - Password minimal 6 dan sama (`app.py:51`, `app.py:53`).
   - Selfie file wajib (`app.py:55`).
   - Validasi kode undangan: `SUDAHBYADMIN` vs format kode normal + cek data master pegawai (`app.py:61`, `app.py:67`, `app.py:69`).
   - Cek email belum terdaftar (`_get_user_by_email`) (`app.py:75`).
   - Validasi file upload (`_validate_upload`) (`app.py:79`).
5. Backend membuka transaksi SQLite (`BEGIN IMMEDIATE`) dan cek duplikasi email di tabel `users` (`app.py:87`, `app.py:89`).
6. Jika kode normal, kuota kode registrasi dikonsumsi via `_consume_employee_registration_code_with_conn` (`app.py:96`, `app.py:1268`).
7. **Role assignment:** user dibuat dengan role tetap `employee` via `_create_user_with_conn(... role="employee")` (`app.py:101`, `app.py:105`, `app.py:851`).
8. **Hashing password:** `_create_user_with_conn` menyimpan `password_hash` dengan `generate_password_hash(password)` sebelum insert ke tabel `users` (`app.py:872`).
9. Selfie disimpan (`_save_upload`), lalu `selfie_path` di-update via `_update_user_selfie_path_with_conn` (`app.py:110`, `app.py:117`).
10. Jika kode `SUDAHBYADMIN`, status master pegawai diaktifkan via `_set_employee_active_with_conn` (`app.py:119`, `app.py:1120`).
11. Transaksi di-commit; jika gagal, rollback DB dan file selfie yang sudah tersimpan dihapus (`app.py:120`, `app.py:93`, `app.py:125`).


## 1B. Glosarium Singkat (Istilah Teknis)

- Form submit: event `submit` pada form HTML.
- Endpoint: URL API yang menerima request, mis. `POST /api/auth/signup`.
- Multipart/form-data: format request untuk kirim file (selfie) + field biasa.
- Validasi frontend: pengecekan input di browser sebelum request dikirim.
- Validasi backend: pengecekan input di server sebelum proses bisnis/DB.
- Transaksi DB: eksekusi SQL atomik (BEGIN/COMMIT/ROLLBACK).
- Role assignment: penetapan `role` saat membuat user (di sini `employee`).
- Hashing password: proses mengubah password menjadi `password_hash` (bcrypt/werkzeug).
- Insert: operasi `INSERT` ke tabel `users`.
- Commit/Rollback: menyimpan atau membatalkan perubahan transaksi.

## Ringkasan Status

- Aturan pendaftaran sudah konsisten dengan dua metode kode (normal vs `SUDAHBYADMIN`).
- Konsumsi kuota kode dan pembuatan akun sudah dalam satu transaksi DB.
- Penyimpanan selfie sudah dilakukan setelah validasi bisnis, dengan rollback file jika gagal.

## 2. Kelemahan, Bug, Kontradiksi, Pelanggaran Aturan/Ketidakkonsistenan Aturan

1. Kontradiksi data master pegawai (aktif vs nonaktif):
   - Status: FIXED (dashboard dan pembuatan profil sama-sama pakai `only_active=False`).
   - Dashboard Pegawai menilai "sudah ada data master pegawai" hanya jika `only_active=True`.
   - Endpoint pembuatan profil menolak jika sudah ada record pegawai, termasuk nonaktif.
   - Akibatnya: akun dengan data pegawai nonaktif terlihat "belum punya data", tetapi tidak bisa membuat data baru.
   - Referensi: `app.py:147-160` dan `app.py:171-175`.

2. Kuota kode pendaftaran/undangan bisa terpotong tanpa akun jadi:
   - Status: FIXED (konsumsi kode + create akun dalam satu transaksi DB).
   - Kode pendaftaran/undangan dikonsumsi sebelum pembuatan akun.
   - Jika insert akun gagal (misalnya race condition atau constraint), kuota sudah terpotong.
   - Referensi: `app.py:78-89` dan `app.py:1134-1162`.

3. Selfie bisa tersimpan walau pendaftaran gagal:
   - Status: FIXED (selfie disimpan setelah validasi; rollback hapus file jika gagal).
   - File selfie disimpan sebelum konsumsi kode pendaftaran/undangan dan sebelum pembuatan akun.
   - Jika kode pendaftaran/undangan invalid/kuota habis, file sudah terlanjur tersimpan (file yatim).
   - Referensi: `app.py:73-81`.

4. Aturan pendaftaran tidak konsisten (kode normal vs `SUDAHBYADMIN`):
   - Status: NEEDS DECISION (tetap seperti sekarang; tergantung kebijakan bisnis).
   - Kode manual mensyaratkan data pegawai aktif sudah ada.
   - Kode pendaftaran/undangan normal tidak mensyaratkan data master pegawai ada.
   - Jika proses bisnis mengharuskan data master pegawai dulu, jalur normal melanggar aturan.
   - Referensi: `app.py:57-68`.

5. Kode `SUDAHBYADMIN` bersifat statis:
   - Status: OPEN (kode statis masih dipakai).
   - Siapa pun yang mengetahui email pegawai yang sudah ada bisa mendaftar tanpa verifikasi tambahan (OTP/approval).
   - Risiko penyalahgunaan/impersonasi jika email pegawai bocor.
   - Referensi: `app.py:59-76`.

6. Email di tabel `employees` tidak unik:
   - Status: OPEN (kolom email belum UNIQUE; aktivasi masih berbasis email).
   - Admin bisa membuat data pegawai dengan email yang sama; signup memakai email sebagai kunci.
   - Saat signup `SUDAHBYADMIN`, aktivasi memakai UPDATE berbasis email sehingga semua record duplikat ikut aktif.
   - Referensi: `app.py:1044-1123` dan `app.py:1622-1633`.


## 2A. Isu Kritis untuk Ditutup sebelum Final

- DEFERRED: Kode statis `SUDAHBYADMIN` masih dipakai (risiko keamanan/impersonation).
  Istilah teknis: security risk (authentication bypass via shared invite code).
- DEFERRED: Email di tabel `employees` belum UNIQUE (risiko integritas data/duplikasi).
  Istilah teknis: data integrity issue (duplicate keys, non-unique natural key).
- NEEDS DECISION: Aturan bisnis kode normal vs `SUDAHBYADMIN` (wajib master data dulu atau tidak).
  Istilah teknis: business rule decision.

## 3. Solusi Perbaikan

1. Konsistenkan aturan data master pegawai:
   - Putuskan apakah semua pendaftaran wajib punya data master pegawai terlebih dahulu.
   - Jika iya, terapkan pengecekan `_employee_by_email(email, only_active=True)` juga pada jalur kode normal.
   - Jika tidak, ubah logika Dashboard Pegawai atau pembuatan profil agar tidak kontradiktif.

2. Bungkus transaksi konsumsi kode + create akun (dipilih):
   - Gunakan transaksi DB agar pengurangan kuota hanya terjadi jika akun berhasil dibuat.
   - Catatan: opsi menunda konsumsi kode setelah akun dibuat tidak dipilih karena berisiko akun terbuat tanpa kuota.

3. Pindahkan penyimpanan selfie setelah semua validasi bisnis lolos:
   - Simpan file selfie hanya setelah kode valid dan kuota tersedia.
   - Tambahkan mekanisme rollback/hapus file jika terjadi kegagalan setelah upload.

4. Samakan indikator "data master pegawai sudah ada" di dashboard dan profil:
   - Jika pakai `only_active=True` di dashboard, maka aturan yang sama dipakai saat membuat profil.
   - Atau tampilkan status "data pegawai nonaktif" agar akun jelas tidak bisa mendaftar ulang.

5. Perketat kode `SUDAHBYADMIN`:
   - Ganti dengan token per-pegawai/per-undangan (one-time, ada masa berlaku) atau tambah approval admin/OTP.
   - Hindari kode statis yang bisa disalahgunakan hanya dengan mengetahui email.

6. Tegakkan keunikan email di `employees`:
   - Tambahkan validasi duplikat saat admin membuat data pegawai.
   - Pertimbangkan constraint unik pada email atau gunakan `employee_id` saat aktivasi/signup.

## 4. Status Uji (Lokal)

- Normal code + email belum ada di data master pegawai: sukses (200).
- Normal code + email sudah ada di data master pegawai: ditolak (400) dengan pesan "Data master pegawai sudah ada. Gunakan kode SUDAHBYADMIN."
- SUDAHBYADMIN + email sudah ada di data master pegawai: sukses (200).
- SUDAHBYADMIN + email belum ada di data master pegawai: ditolak (400) dengan pesan "Data master pegawai belum ada. Hubungi admin untuk input data."

Catatan: Tes diulang setelah implementasi transaksi konsumsi kode + create akun, hasilnya tetap konsisten.
Catatan tambahan: Tes diulang setelah perbaikan alur penyimpanan selfie (sesudah validasi bisnis), hasilnya tetap konsisten.
Catatan tambahan: Pegawai yang diinput admin di master data dibuat nonaktif terlebih dahulu; saat signup dengan kode `SUDAHBYADMIN` status berubah aktif; admin tetap bisa menonaktifkan kembali untuk memblokir akses dashboard pegawai.
Catatan tambahan: Uji manual modal “Lengkapi Data Pegawai” sudah dijalankan dan sesuai pada tiga kasus (kode normal tanpa master data, kode normal dengan master data, dan `SUDAHBYADMIN` dengan master data).

## Checklist

- [x] Aturan pendaftaran: normal code untuk pegawai baru, `SUDAHBYADMIN` untuk pegawai yang sudah diinput admin.
- [x] Indikator Dashboard Pegawai konsisten dengan pembuatan profil.
- [x] Transaksi konsumsi kode + create akun sudah aman (atomic).
- [x] Penyimpanan selfie setelah validasi bisnis + rollback file saat gagal.
- [x] Uji lokal: 4 skenario signup (normal/`SUDAHBYADMIN`).
- [x] Aturan status pegawai: default nonaktif saat ditambah admin, aktif setelah signup `SUDAHBYADMIN`, admin bisa disable ulang untuk blok akses.
- [x] Uji manual di UI: modal "Lengkapi Data Pegawai" muncul hanya untuk kode normal tanpa data master pegawai.
- [x] Uji manual di UI: modal tidak bisa ditutup sebelum form selesai.
- [x] Uji manual di UI: presensi ditolak jika data master pegawai belum lengkap.

## Update Status Implementasi (Client/Site/Assignment/Policy)

Sumber: audit terkini dari `docs/client_entity.md`.

### Implementasi yang sudah ada
- [x] `sites.client_id` + migrasi dari `client_name`, serta FK `sites.client_id -> clients.id` sudah diterapkan.
- [x] `assignments` tersedia (tabel + CRUD + UI) dan dipakai untuk penempatan aktif.
- [x] `attendance_policies` tersedia (tabel + CRUD) dan dipakai saat validasi presensi.
- [x] `client_contacts` tersedia (tabel + CRUD + UI di client profile).
- [x] `timezone` dan `work_mode` sudah tersedia di `sites` (schema + UI).
- [x] Dashboard pegawai menampilkan client/site aktif dari assignment.

### Gap yang masih ada
- [ ] Modul kontrak/SLA/billing belum ada (UI + backend).
- [ ] Data default policy per client belum diisi (perlu seeding/operasional).
- [ ] Legacy `client_name` dan `employee_site` masih tersimpan (perlu rencana cleanup jika tidak dibutuhkan).

### Catatan Migrasi
- [x] Foreign key enforcement aktif (PRAGMA foreign_keys=ON) dan migrasi rebuild tabel `sites` dilakukan saat init bila FK belum ada.
