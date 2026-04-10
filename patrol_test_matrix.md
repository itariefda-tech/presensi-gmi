# Test Matrix Patroli Guard Tour

Matrix ini dipakai untuk verifikasi kombinasi mode keamanan patroli:
- `strict_mode`
- `require_selfie`
- `require_gps`

## Aturan Verifikasi
- `strict_mode=ON`: scan wajib urut.
- `strict_mode=OFF`: scan boleh tidak urut, tetapi checkpoint yang sudah tervalidasi tidak boleh di-scan ulang.
- `require_selfie=ON`: setiap scan checkpoint wajib selfie.
- `require_gps=ON`: setiap scan checkpoint wajib validasi radius GPS.

## Matrix Kombinasi
- [ ] `strict=OFF`, `selfie=OFF`, `gps=OFF`
  - Ekspektasi: scan acak valid; tanpa selfie valid; tanpa GPS valid; scan ulang checkpoint yang sama ditolak.
- [ ] `strict=OFF`, `selfie=OFF`, `gps=ON`
  - Ekspektasi: scan acak valid; GPS wajib valid; selfie opsional; scan ulang checkpoint yang sama ditolak.
- [ ] `strict=OFF`, `selfie=ON`, `gps=OFF`
  - Ekspektasi: scan acak valid; selfie wajib; GPS opsional; scan ulang checkpoint yang sama ditolak.
- [ ] `strict=OFF`, `selfie=ON`, `gps=ON`
  - Ekspektasi: scan acak valid; selfie wajib; GPS wajib valid; scan ulang checkpoint yang sama ditolak.
- [ ] `strict=ON`, `selfie=OFF`, `gps=OFF`
  - Ekspektasi: scan harus berurutan; selfie opsional; GPS opsional.
- [ ] `strict=ON`, `selfie=OFF`, `gps=ON`
  - Ekspektasi: scan harus berurutan; GPS wajib valid; selfie opsional.
- [ ] `strict=ON`, `selfie=ON`, `gps=OFF`
  - Ekspektasi: scan harus berurutan; selfie wajib; GPS opsional.
- [ ] `strict=ON`, `selfie=ON`, `gps=ON`
  - Ekspektasi: scan harus berurutan; selfie wajib; GPS wajib valid.

## Checklist Eksekusi Uji
- [ ] Siapkan 1 rute dengan minimal 3 checkpoint (QR/NFC valid).
- [ ] Jalankan uji untuk 8 kombinasi di atas.
- [ ] Catat hasil API (`ok`, `message`, `validation_status`) untuk tiap kombinasi.
- [ ] Pastikan `dashboard client admin` (monitoring/rekap) konsisten dengan hasil scan.
- [ ] Pastikan `dashboard pegawai` (mode keamanan, hint selfie, status toast) konsisten dengan hasil scan.
