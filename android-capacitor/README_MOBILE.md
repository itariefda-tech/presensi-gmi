# Android Capacitor Wrapper for Presensi Web App

## Tujuan
Membungkus web app HRIS/Presensi dalam aplikasi Android native (in-app WebView, bukan browser eksternal) menggunakan Capacitor.

## Build & Run

1. Install Node.js (LTS) dan Android Studio.
2. Masuk ke folder ini:
   ```powershell
   cd android-capacitor
   ```
3. Install dependencies:
   ```powershell
   npm install
   ```
4. Set URL web app:
   - Default production: https://absensi.gajiku.online (sudah diatur di `capacitor.config.ts`)
   - Untuk development lokal:
     - Edit `capacitor.config.ts` → ganti `DEV_URL` ke http://10.0.2.2:5020 (emulator) atau http://IP_LAN:5020 (device)
     - Atau buat file `.env` dan set `DEV_URL` jika ingin override
   - Pastikan mode dev/prod sesuai kebutuhan sebelum build APK/AAB.
5. Build web (jika ada), lalu sync:
   ```powershell
   npx cap sync android
   ```
6. Buka Android Studio:
   ```powershell
   npx cap open android
   ```
7. Build & run APK dari Android Studio (atau gunakan emulator/device).

## Troubleshooting

- Jika aplikasi membuka browser eksternal:
  - Pastikan tidak ada `Browser.open()` atau `window.open()` di kode.
  - Cek `capacitor.config.ts` → `server.url` harus diisi.
  - Cek intent filter AndroidManifest.
- Jika blank/putih:
  - Cek network_security_config, CSP, mixed content.
- Login/session tidak nempel:
  - Pastikan pakai HTTPS, cek cookie SameSite.
- Kamera/GPS tidak jalan:
  - Pastikan permission sudah diizinkan di AndroidManifest dan runtime.

## Struktur Penting
- `capacitor.config.ts` — konfigurasi URL, allowNavigation, scheme.
- `android/` — project native Android.
- `src/` — (opsional) asset offline/fallback. Contoh: `src/offline.html` untuk tampilan "Tidak ada internet" jika WebView gagal load.

## Catatan
- Semua perubahan wrapper hanya di folder ini.
- Tidak mengubah core Flask/web kecuali mutlak perlu (misal header minimal).

## Android Permissions Penting
- Pastikan AndroidManifest.xml mengandung:
  - `<uses-permission android:name="android.permission.INTERNET" />`
  - `<uses-permission android:name="android.permission.CAMERA" />` (jika upload foto/kamera)
  - `<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />` (jika pakai GPS)
  - (Opsional) `<uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />` (Android 13+)
- Untuk upload file/kamera/location di WebView, pastikan permission runtime sudah di-handle (lihat plugin Capacitor terkait jika perlu).

## Audit Kode Wrapper
- Pastikan TIDAK ADA:
  - `Browser.open()`
  - `window.open()` ke URL utama
  - index.html yang redirect ke browser
- Semua URL utama harus dimuat di WebView (in-app), bukan browser eksternal.
