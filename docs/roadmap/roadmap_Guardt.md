# Roadmap Penyempurnaan Patroli Guard Tour

## Hasil Lacak Orphan / Mock / Logic Belum Nyambung
- **RESOLVED:** `Strict sequence validation` sudah terhubung ke validasi urutan scan.
  - `strict_mode=ON`: scan wajib urut.
  - `strict_mode=OFF`: scan boleh tidak urut, tetapi checkpoint yang sudah tervalidasi tidak boleh di-scan ulang.
- **MOCK:** pesan `Upgrade Pro+` sudah muncul di UI/API limit checkpoint, tetapi belum ada alur upgrade/billing/subscription yang bisa dijalankan pengguna dari modul patroli.
- **RESOLVED:** panel `Data Structure Snapshot` disembunyikan dari UI operasional pengguna.

## Progress Label di UI (Masih Aktif)
- [x] Client Admin: label `Upgrade Pro+ = MOCK CTA` pada pesan limit checkpoint.
- [x] Dashboard Pegawai: label `Upgrade Pro+ (MOCK CTA)` pada hint batas checkpoint.

## Checkpoint Penyempurnaan Lanjutan
- [x] Sambungkan `strict_mode` ke validasi urutan scan (aturan urutan harus mengikuti nilai toggle).
- [x] Definisikan perilaku non-strict yang jelas (mis. tetap valid bila scan tidak berurutan, dengan konsekuensi status/progress terukur).
- [x] Tambahkan test matrix patroli: `strict on/off` x `selfie on/off` x `gps on/off` (lihat `patrol_test_matrix.md`).
- [ ] Sediakan alur upgrade nyata (route/API + UI action), atau ganti copy agar tidak menjadi CTA palsu.
- [x] Ubah `Data Structure Snapshot` menjadi panel operasional (filter, export, drilldown) atau sembunyikan dari pengguna non-teknis.
