# Audit Kesiapan Produksi Akhir

## 1. Logika & Alur Kontrol
- [x] Masalah: Multi check-in/check-out diizinkan tanpa penegakan invariant per hari. Lokasi: `app.py:355` (`attendance_checkin`), `app.py:425` (`attendance_checkout`). Keparahan: medium. Dampak: duplikasi atau kontradiksi data presensi dan kesalahan perhitungan payroll. Rekomendasi perbaikan: terapkan satu check-in dan satu check-out per hari per pegawai (atau aturan multi-shift yang eksplisit) dengan pemeriksaan transaksi.
- [x] Masalah: Checkout dapat dilakukan tanpa check-in sebelumnya. Lokasi: `app.py:425` (`attendance_checkout`). Keparahan: medium. Dampak: transisi status presensi tidak valid dan kesalahan pelaporan. Rekomendasi perbaikan: validasi status presensi terakhir sebelum mengizinkan checkout.
- [x] Masalah: Tidak ada pencegahan multiple assignment aktif; sistem memilih yang paling baru berdasarkan start_date. Lokasi: `app.py:1463` (`_get_active_assignment`). Keparahan: medium. Dampak: pemilihan policy/site tidak deterministik saat assignment tumpang tindih. Rekomendasi perbaikan: paksa hanya satu assignment aktif per pegawai melalui validasi dan constraint.

## 2. Integritas Status & Alur Kerja
- [x] Masalah: Approval manual attendance mengubah status dan menambah attendance dalam transaksi terpisah. Lokasi: `app.py:4849` (`manual_attendance_approve`), `app.py:3880` (`_approve_manual_request`), `app.py:3912` (`_insert_manual_attendance_record`). Keparahan: high. Dampak: race condition dapat menyebabkan insert ganda atau request approved tanpa record attendance. Rekomendasi perbaikan: bungkus approval dan insert attendance dalam satu transaksi dengan re-check status.
- [x] Masalah: Endpoint API mengizinkan pengajuan manual attendance walau kebijakan UI memblokir manager. Lokasi: `app.py:505` (`attendance_manual`) vs `app.py:3592` (`_can_submit_manual`). Keparahan: medium. Dampak: bypass kebijakan dan inkonsistensi aturan workflow antara UI dan API. Rekomendasi perbaikan: terapkan `_can_submit_manual` pada route API.
- [x] Masalah: Upload selfie presensi disimpan namun tidak dicatat di database. Lokasi: `app.py:355` (`attendance_checkin`), `app.py:425` (`attendance_checkout`), `app.py:3292` (skema tabel attendance). Keparahan: medium. Dampak: file orphaned dan bukti audit hilang. Rekomendasi perbaikan: tambahkan kolom path selfie di attendance atau hentikan penyimpanan jika tidak dipersist.

## 3. Otorisasi, Peran & Kebijakan
- [x] Masalah: Tidak ada proteksi CSRF untuk form POST berbasis sesi. Lokasi: `templates/dashboard/admin_settings.html:21` (dan form POST lain) dengan route terkait di `app.py`. Keparahan: high. Dampak: CSRF bisa memicu aksi admin tanpa izin. Rekomendasi perbaikan: aktifkan token CSRF dan validasi pada semua route yang mengubah state.
- [x] Masalah: User nonaktif tetap bisa akses karena session tidak memvalidasi `is_active`. Lokasi: `app.py:827` (`_current_user`), `app.py:842` (`_require_role`). Keparahan: high. Dampak: user yang dinonaktifkan masih bisa beroperasi sampai logout. Rekomendasi perbaikan: cek `is_active` ke database di setiap request atau cabut sesi saat dinonaktifkan.
- [x] Masalah: Otoritas approval manager_operational diblokir jika ada supervisor aktif, tanpa mempertimbangkan konteks assignment. Lokasi: `app.py:3608` (`_can_approve_leave`), `app.py:3620` (`_can_approve_manual`). Keparahan: medium. Dampak: deadlock approval saat supervisor ada tetapi tidak bisa approve. Rekomendasi perbaikan: basis approval pada scope/assignment, bukan sekadar keberadaan role global.
- [x] Masalah: Daftar leave pending dapat diakses semua admin role, termasuk yang tidak punya hak approval. Lokasi: `app.py:652` (`leave_pending`). Keparahan: low. Dampak: paparan data leave pegawai yang tidak perlu. Rekomendasi perbaikan: batasi ke role approver atau definisikan kebijakan eksplisit.

## 4. Integritas Data & Database
- [x] Masalah: Tabel employees tidak memiliki UNIQUE constraint untuk `email`, `nik`, atau `no_hp`. Lokasi: `app.py:3096` (skema employees). Keparahan: high. Dampak: identitas duplikat menyebabkan ambiguitas login dan mapping yang salah. Rekomendasi perbaikan: tambahkan UNIQUE index dan remediasi duplikasi data yang sudah ada.
- [x] Masalah: Tabel relasional inti tidak memiliki foreign key (assignments, supervisor_sites, employee_site, attendance, manual_attendance_requests). Lokasi: `app.py:3161` (supervisor_sites), `app.py:3171` (employee_site), `app.py:3181` (assignments), `app.py:3260` (manual_attendance_requests), `app.py:3292` (attendance). Keparahan: medium. Dampak: record orphan dan join yang inkonsisten. Rekomendasi perbaikan: tambah foreign key dan bersihkan record orphan.
- [x] Masalah: `manual_attendance_requests.created_by_user_id` menyimpan email walau namanya user ID. Lokasi: `app.py:3260` (skema), `app.py:3818` (`_create_manual_request`). Keparahan: low. Dampak: kebingungan dan join rusak bila ID numerik diterapkan nanti. Rekomendasi perbaikan: ganti nama field atau simpan ID numerik.
- [x] Masalah: Tabel attendance tidak memiliki constraint untuk mencegah multi check-in/out per hari per pegawai. Lokasi: `app.py:3292` (skema attendance). Keparahan: medium. Dampak: perhitungan presensi tidak konsisten. Rekomendasi perbaikan: tambahkan unique constraint atau enforce di logika dengan transaksi.

## 5. Sistem File & Kebersihan Kode
- [x] Masalah: File database runtime tersimpan di repo (`app.db`, `presensi.db`). Lokasi: root repository. Keparahan: high. Dampak: kebocoran data dan drift konfigurasi antar environment. Rekomendasi perbaikan: keluarkan dari repo, tambahkan ke `.gitignore`, dan kelola data di luar version control.
- [x] Masalah: Helper `_role_from_email` tidak digunakan (dead code). Lokasi: `app.py:802`. Keparahan: low. Dampak: beban pemeliharaan dan kebingungan soal penentuan role. Rekomendasi perbaikan: hapus atau hubungkan ke alur yang terdokumentasi.
- [x] Masalah: Asset gambar demo dipakai di UI produksi. Lokasi: `templates/dashboard/employee.html` dan `templates/dashboard/base.html` (avatar default). Keparahan: low. Dampak: branding tidak profesional atau risiko IP. Rekomendasi perbaikan: ganti dengan aset produksi atau hapus.

## 6. Kesiapan UI & UX
- [x] Masalah: Teks di admin overview menyatakan fitur belum diimplementasi padahal dashboard sudah menyediakan pembuatan user. Lokasi: `templates/dashboard/admin_overview.html:140`. Keparahan: low. Dampak: kebingungan pengguna dan ketidakjelasan status readiness. Rekomendasi perbaikan: sesuaikan copy dengan fungsi yang ada.

## 7. Stabilitas & Keamanan Produksi
- [x] Masalah: Default secret key Flask di-hardcode sebagai fallback. Lokasi: `app.py:30` (`create_app`). Keparahan: blocker. Dampak: integritas sesi terancam jika secret environment tidak diset. Rekomendasi perbaikan: wajibkan `FLASK_SECRET` di produksi dan fail fast jika tidak ada.
- [x] Masalah: Seed user dan default password di-hardcode dalam code dan dokumentasi. Lokasi: `app.py:766` (`SEED_USERS`), `app.py:773` (`DEFAULT_RESET_PASSWORD`), `templates/README.md:17`. Keparahan: blocker. Dampak: kredensial diketahui di produksi. Rekomendasi perbaikan: hapus seed untuk produksi atau gate dengan flag environment; paksa rotasi password.
- [x] Masalah: Endpoint reset password adalah stub demo tanpa alur reset nyata. Lokasi: `app.py:186` (`forgot`). Keparahan: high. Dampak: user tidak bisa recovery akun secara aman. Rekomendasi perbaikan: implementasikan reset dengan token time-bound atau OTP.
- [x] Masalah: Validasi QR memakai prefix statis dan aturan demo. Lokasi: `app.py:4057` (`_validate_qr_data`). Keparahan: high. Dampak: QR mudah dipalsukan. Rekomendasi perbaikan: gunakan token QR yang ditandatangani dan time-bound.
- [x] Masalah: Logout menggunakan endpoint GET. Lokasi: `app.py:350` (`logout`). Keparahan: low. Dampak: logout tidak sengaja atau dipicu CSRF. Rekomendasi perbaikan: ubah ke POST dengan proteksi CSRF.
- [x] Masalah: Audit log tidak mencakup alur kritikal (login, attendance, approval cuti, perubahan password). Lokasi: `app.py:1239` (`_log_audit_event`) dan tidak digunakan di route auth/attendance. Keparahan: medium. Dampak: jejak audit untuk insiden keamanan terbatas. Rekomendasi perbaikan: tambahkan audit event untuk auth, attendance, dan approval.

## 8. Runbook Operasional

- Masalah operasional: Saat running image di NAS, pastikan akun seed tersedia. Default seed menyediakan `hrd@gmi.com / hrd123`. Jika ingin override, jalankan container dengan `SEED_USERS_JSON`:
  1. Build image dari root repo: `docker build -t presensi-app .`.
  2. Jalankan container (opsional: override seed):
     ```
     docker run -d \
       --name presensi-app \
       -e ENABLE_SEED_DATA=1 \
       -e SEED_USERS_JSON='[{"email":"hrd@gmi.com","name":"HR Superadmin","role":"hr_superadmin","password":"hrd123"}]' \
       -p 5050:5050 \
       presensi-app
     ```
  3. Login pertama pakai `hrd@gmi.com / hrd123`, lalu segera ubah password melalui menu profil.

- Masalah networking: reverse proxy (hosting_web) perlu bisa reach container, sehingga setelah container jalan pastikan ia terhubung ke network itu:
  ```
  docker network connect hosting_web presensi-app
  ```
  Setelah koneksi, Cloudflare atau Nginx yang run di `hosting_web` akan melihat service dan akses `absensi.gajiku.online` tidak lagi mengembalikan 502.
