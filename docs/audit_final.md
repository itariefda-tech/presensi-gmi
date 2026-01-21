---
# Audit Final (Demo)

Tanggal: 2026-01-21

## Temuan & Perbaikan
- Edit client gagal tersimpan karena validasi konflik nama/legal selalu aktif; kini hanya dicek bila nama/legal berubah.
- Pesan validasi server tidak terlihat di dashboard; sekarang tampil melalui flash alert global.
- Modal edit client ditambah scroll agar field bawah tetap bisa diakses di layar kecil.

## Catatan Deploy Demo
- QR payload butuh env `QR_SECRET`; app harus restart dari shell yang memuat env baru.
- QR generator tergantung library QR dari CDN; jika CDN diblok, QR tidak tampil dan perlu file lokal.

