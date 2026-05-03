# ROADMAP - API ACCESS ADD-ON TOGGLE

Tujuan: Membuat add-on **API access** bisa diaktifkan/nonaktifkan secara jelas dari UI tier/add-on, tersimpan per client, terhubung ke endpoint API, dan aman untuk production.

---

## PHASE 1 - AUDIT KONDISI SAAT INI
Tujuan: Pastikan semua titik yang sudah ada dipetakan sebelum implementasi toggle.

### Inventarisasi Add-on
- [x] Cek konstanta `ADDON_API_ACCESS`.
- [x] Cek mapping alias add-on untuk `api`, `api_access`, dan label "API access".
- [x] Cek apakah API access termasuk add-on global, per-client, atau excluded dari bundle Enterprise.
- [x] Cek struktur data `clients.addons`.
- [x] Cek struktur data `client_addons`.

### Inventarisasi UI
- [x] Cek toggle API access di halaman owner/add-ons.
- [x] Cek toggle API access di halaman admin settings subscription/add-ons.
- [x] Cek apakah checkbox API access masih disabled.
- [x] Cek apakah label, helper text, dan state aktif/nonaktif sudah jelas.

### Inventarisasi Endpoint
- [x] Cek endpoint API yang harus dilindungi API access.
- [x] Cek gate `_require_client_addon(... ADDON_API_ACCESS ...)`.
- [x] Cek response ketika add-on belum aktif.
- [x] Cek behavior untuk admin, client admin, dan token/API user.

### Temuan Phase 1
- [x] `ADDON_API_ACCESS = "api_access"` sudah tersedia di `app.py`.
- [x] Alias `api` dan `api_access` sudah mengarah ke `ADDON_API_ACCESS`.
- [x] API access masuk `ADDON_ALLOWED` dan `ADDON_OWNER_ORDER`.
- [x] API access termasuk `ADDON_ENTERPRISE_EXCLUDED`, sehingga tidak otomatis aktif hanya karena Enterprise bundle.
- [x] Toggle owner tersedia di landing owner add-on (`templates/index.html`) sebagai `data-owner-addon="api_access"`.
- [x] Toggle owner di admin settings tersedia sebagai `data-owner-addon value="api_access"`, tetapi default disabled sampai owner unlock.
- [x] Toggle per client tersedia di admin settings subscription lewat loop `client_addon_options`.
- [x] Endpoint `/api/v1/attendance` sudah memakai gate `_require_client_addon(user, ADDON_API_ACCESS, "API access", client_id)`.
- [x] Jika `client_id` tidak tersedia, endpoint API access mengembalikan validasi `client_id wajib untuk API access`.
- [x] Behavior client role sudah diarahkan memakai scope `user.client_id`/`user.site_id`.

---

## PHASE 2 - DATA MODEL & SOURCE OF TRUTH
Tujuan: Tentukan tempat penyimpanan toggle yang konsisten.

### Source of Truth
- [x] Tetapkan apakah API access disimpan di `clients.addons`, `client_addons`, atau keduanya untuk kompatibilitas.
- [x] Buat aturan prioritas pembacaan add-on:
  - [x] `client_addons` sebagai sumber utama.
  - [x] `clients.addons` sebagai fallback legacy.
  - [x] Global add-ons hanya untuk owner/admin global bila memang diperlukan.

### Migration Guard
- [x] Pastikan tabel `client_addons` tersedia.
- [x] Pastikan index `client_addons(client_id, addon_key, is_enabled)` tersedia.
- [x] Pastikan `clients.addons` tetap ada untuk backward compatibility.
- [x] Tambahkan migration sync jika dibutuhkan dari `clients.addons` ke `client_addons`.

### Helper Backend
- [x] Pastikan helper `_list_client_addons(client_id)` membaca API access.
- [x] Pastikan helper `_set_client_addons(client_id, addons)` dapat menyimpan API access.
- [x] Pastikan helper `has_addon(client, ADDON_API_ACCESS)` tetap kompatibel.
- [x] Pastikan `_client_feature_enabled(user, ADDON_API_ACCESS, client_id)` mengembalikan status benar.

### Implementasi Phase 2
- [x] API access ditambahkan ke `CLIENT_ADDON_OPTIONS`, sehingga helper per-client dapat membaca/menyimpan `api_access`.
- [x] `_list_client_addons(client_id)` membaca `client_addons` sebagai sumber utama dan hanya fallback ke `clients.addons` bila client belum punya baris add-on di `client_addons`.
- [x] `_set_client_addons(client_id, addons)` menyimpan status ke `client_addons` dan menyinkronkan `clients.addons` untuk backward compatibility.
- [x] `has_addon(client, ADDON_API_ACCESS)` memakai helper per-client agar data legacy yang stale tidak mengalahkan status nonaktif di `client_addons`.
- [x] `_init_db()` menyalin add-on legacy dari `clients.addons` ke `client_addons` hanya untuk baris yang belum ada, supaya status nonaktif di `client_addons` tetap menang.

---

## PHASE 3 - OWNER GLOBAL ADD-ON TOGGLE
Tujuan: Owner dapat mengatur apakah add-on API access tersedia sebagai fitur yang bisa dipakai.

### API Owner
- [x] Validasi `GET /api/owner/addons` mengembalikan status `api_access`.
- [x] Validasi `POST /api/owner/addons/verify` membuka akses pengaturan owner.
- [x] Validasi `POST /api/owner/addons` bisa menyimpan `api_access`.
- [x] Pastikan `api_access` tidak otomatis aktif karena Enterprise bundle jika memang excluded.

### UI Owner
- [x] Aktifkan checkbox API access di owner add-ons jika saat ini disabled.
- [x] Tambahkan helper text bahwa API access adalah add-on terpisah.
- [x] Tambahkan visual state aktif/nonaktif.
- [x] Tambahkan loading state saat menyimpan.
- [x] Tambahkan error state bila owner belum verify.

### Validasi
- [x] Toggle ON API access tersimpan.
- [x] Toggle OFF API access tersimpan.
- [x] Refresh halaman tetap menampilkan state terakhir.
- [x] Tidak mengubah add-on lain tanpa sengaja.

### Implementasi Phase 3
- [x] Owner add-on API `GET/verify/POST` sudah diverifikasi lewat integration test.
- [x] Panel owner add-on di settings sekarang menampilkan helper text khusus API access dan loading state saat unlock/save.
- [x] `API access` tetap excluded dari auto-enable Enterprise bundle, sehingga owner/global hanya menjadi master availability.

---

## PHASE 4 - CLIENT/SUBSCRIPTION ADD-ON TOGGLE
Tujuan: Admin dapat mengaktifkan API access untuk client tertentu.

### UI Admin Settings
- [x] Tampilkan API access sebagai add-on per client.
- [x] Pastikan checkbox API access tidak disabled jika owner/global mengizinkan.
- [x] Jika owner/global tidak mengizinkan, tampilkan disabled dengan alasan.
- [x] Tambahkan deskripsi singkat:
  - [x] "Membuka endpoint API untuk integrasi eksternal."
  - [x] "Butuh token/API credential."
  - [x] "Akses tetap dibatasi scope client."

### Form Save
- [x] Pastikan submit settings membawa `addons=["api_access"]` saat dicentang.
- [x] Pastikan `_set_client_addons(client_id, addons)` menyimpan status.
- [x] Pastikan `clients.addons` ikut disinkronkan jika masih dipakai UI lama.
- [x] Pastikan audit log tercatat saat add-on berubah.

### State UI
- [x] Jika add-on aktif, tampilkan badge "Active".
- [x] Jika add-on nonaktif, tampilkan badge "Inactive".
- [x] Jika belum tersedia dari owner/global, tampilkan badge "Unavailable".

### Implementasi Phase 4
- [x] Subscription settings per client sekarang memaksa `API access` hanya bisa dicentang saat owner/global sudah aktif.
- [x] Perubahan subscription API access dicatat ke audit log `client_subscription`.
- [x] Panel yang sama sekarang menampilkan credential management dan status pemakaian API access per client.

---

## PHASE 5 - API GATING & ACCESS CONTROL
Tujuan: Endpoint API hanya bisa digunakan jika add-on API access aktif untuk client terkait.

### Endpoint Guard
- [x] Pastikan semua endpoint API publik/integrasi memanggil guard API access.
- [x] Pastikan guard memakai `client_id` yang resolved, bukan input mentah.
- [x] Pastikan client role tidak bisa akses client lain.
- [x] Pastikan admin role tetap butuh client scope bila endpoint membutuhkan `client_id`.

### Response Contract
- [x] Jika add-on nonaktif, return `403`.
- [x] Jika `client_id` tidak dikirim, return `400`.
- [x] Jika client tidak ditemukan, return `404` atau `400` sesuai pola existing.
- [x] Jika token/API auth invalid, return `401`.
- [x] Response error harus konsisten dan tidak membocorkan data client lain.

### Scope
- [x] API user/client token hanya melihat data client sendiri.
- [x] Site filter hanya boleh site milik client tersebut.
- [x] Employee filter hanya boleh employee milik client/site tersebut.

### Implementasi Phase 5
- [x] `/api/v1/attendance` kini menerima token per client dan tetap memaksa scope client/site/employee hasil resolve, bukan query mentah.
- [x] Invalid token mengembalikan `401`, add-on nonaktif mengembalikan `403`, dan client yang tidak ada mengembalikan `404`.
- [x] Request API yang lolos atau ditolak setelah auth dicatat ke `api_access_logs` untuk audit operasional.

---

## PHASE 6 - API TOKEN / CREDENTIAL MANAGEMENT
Tujuan: API access tidak hanya toggle, tapi punya credential yang bisa dikelola aman.

### Data Credential
- [x] Tentukan lokasi penyimpanan token:
  - [x] token per client untuk produksi.
- [x] Simpan hash token, bukan token plaintext.
- [x] Tambahkan `created_at`, `last_used_at`, dan `revoked_at`.
- [x] Tambahkan label token, misalnya "ERP Integration".

### UI Credential
- [x] Tambahkan panel "API Credentials" pada client/add-on settings.
- [x] Tombol generate token.
- [x] Tombol revoke token.
- [x] Tampilkan token hanya sekali saat dibuat.
- [x] Tampilkan last used.

### Security
- [x] Token minimal 32 byte random.
- [x] Jangan log token plaintext.
- [x] Masking token di UI.
- [x] Audit log saat generate/revoke token.

### Implementasi Phase 6
- [x] Tabel `api_client_tokens` dibuat untuk menyimpan token per client beserta hash, prefix, label, `last_used_at`, dan `revoked_at`.
- [x] Generate token hanya menampilkan plaintext sekali, lalu UI hanya menampilkan prefix ter-mask.
- [x] Revoke token langsung membuat token tidak valid untuk endpoint API v1.

---

## PHASE 7 - API ACCESS DASHBOARD
Tujuan: Admin/client tahu API access sedang aktif dan digunakan.

### Status Dashboard
- [x] Tampilkan API access status per client.
- [x] Tampilkan jumlah token aktif.
- [x] Tampilkan last API call.
- [x] Tampilkan endpoint yang paling sering dipakai.

### Usage Log
- [x] Log request API penting.
- [x] Simpan client_id, endpoint, method, status_code.
- [x] Simpan timestamp.
- [x] Simpan actor/token label, bukan token.
- [x] Tambahkan filter tanggal.

### Limit & Quota
- [x] Tambahkan rate limit per token/client.
- [x] Tambahkan quota harian/bulanan bila diperlukan.
- [x] Tampilkan warning jika mendekati limit.

### Implementasi Phase 7
- [x] Ringkasan status API access sekarang tersedia langsung di row subscription client agar admin bisa melihat status aktif, token, last call, dan endpoint teratas.
- [x] Tabel `api_access_logs` menyimpan jejak pemakaian per client/token tanpa menyimpan plaintext token.
- [x] Warning limit harian ditampilkan dari agregasi usage log per client dan per token.

---

## PHASE 8 - UI/UX HARDENING
Tujuan: Toggle API access mudah dipahami dan tidak membingungkan.

### UX Copy
- [x] Gunakan label konsisten "API access".
- [x] Jelaskan bahwa API access adalah add-on integrasi eksternal.
- [x] Jelaskan risiko keamanan jika token bocor.
- [x] Jelaskan bahwa add-on harus aktif per client.

### UI State
- [x] Loading state saat toggle disimpan.
- [x] Empty state jika belum ada token.
- [x] Disabled state jika tier/client belum eligible.
- [x] Confirmation dialog saat menonaktifkan API access.
- [x] Confirmation dialog saat revoke token.

### Guard UX
- [x] Jika API access dimatikan, tampilkan warning token tidak bisa dipakai.
- [x] Jika token masih aktif lalu add-on dimatikan, token tidak valid sampai add-on aktif lagi.
- [x] Jika add-on dinyalakan kembali, token lama mengikuti kebijakan:
  - [x] tetap aktif, atau
  - [ ] wajib generate ulang.

### Implementasi Phase 8
- [x] Tab subscription sekarang punya copy yang konsisten untuk API access, termasuk catatan risiko jika token bocor.
- [x] Form subscription, generate token, dan revoke token sekarang punya loading state ringan dan confirmation dialog saat menonaktifkan akses.
- [x] State disabled kini jelas ketika owner/global off atau package client belum Enterprise.
- [x] Token lama tetap disimpan saat add-on dimatikan, tetapi request API tetap ditolak sampai client mengaktifkan kembali API access.

---

## PHASE 9 - TESTING
Tujuan: Pastikan toggle, gating, dan credential aman.

### Unit/Integration Test
- [x] Test toggle owner API access ON/OFF.
- [x] Test toggle client API access ON/OFF.
- [x] Test endpoint API return `403` saat add-on OFF.
- [x] Test endpoint API return `200` saat add-on ON dan token valid.
- [x] Test client tidak bisa akses client lain.
- [x] Test site scope tidak bocor.
- [x] Test employee scope tidak bocor.
- [x] Test token revoke.
- [x] Test token plaintext tidak tersimpan.

### Regression Test
- [x] Pastikan add-on lain tidak berubah saat API access di-toggle.
- [x] Pastikan Enterprise excluded logic tetap benar.
- [x] Pastikan UI owner settings tetap bisa save add-on lain.
- [x] Pastikan admin settings subscription tetap bisa save package/add-ons.

### Implementasi Phase 9
- [x] Test API access kini mencakup owner toggle, client toggle, token hashing, token revoke, dan endpoint scope enforcement.
- [x] Regression test memastikan add-on global lain dan add-on client lain tidak hilang saat API access berubah.
- [x] Filter tanggal usage log juga diuji dari halaman subscription.

---

## PHASE 10 - DOCUMENTATION & RELEASE
Tujuan: Fitur siap dipakai tim internal dan client.

### Documentation
- [x] Update `docs/API_SPEC_ENTERPRISE.md`.
- [x] Tambahkan bagian "Mengaktifkan API access".
- [x] Tambahkan contoh request API dengan token.
- [x] Tambahkan contoh error jika add-on belum aktif.
- [x] Tambahkan panduan rotate/revoke token.

### Release Checklist
- [x] Migration sudah aman dijalankan ulang.
- [x] Toggle owner sudah diuji.
- [x] Toggle client sudah diuji.
- [x] API gating sudah diuji.
- [x] Audit log aktif.
- [x] Rate limit aktif atau masuk backlog jelas.
- [x] Dokumentasi tersedia.

### Implementasi Phase 10
- [x] `docs/API_SPEC_ENTERPRISE.md` sekarang memuat alur aktivasi API access, contoh request token, contoh error, dan panduan rotate/revoke.
- [x] Regression test memastikan migration `API access` aman dijalankan ulang tanpa menduplikasi token atau merusak state add-on.
- [x] Release checklist yang bisa diverifikasi lokal sudah ditutup lewat test integration, audit log, dan rate limit yang aktif di kode.

### Rollout
- [ ] Aktifkan di staging.
- [ ] Test dengan 1 client pilot.
- [ ] Monitor log API.
- [ ] Aktifkan production bertahap.
