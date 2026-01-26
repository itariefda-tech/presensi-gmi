# Debug Guide - Check-in GPS Mode

## Untuk Menemukan Bug

### Step 1: Buka Browser DevTools
- Tekan `F12` atau `Ctrl+Shift+I`
- Pilih tab `Console`

### Step 2: Test Check-in dengan GPS Mode
1. Pastikan dashboard pegawai sudah terbuka
2. Pastikan:
   - Location button **HIJAU** (aktif)
   - Metode dipilih: **GPS** (bukan GPS+Selfie)
   - Badge status: **"Siap Absen"** (bukan "Belum siap")
3. Klik tombol **"Masuk"**

### Step 3: Lihat Debug Alert
- Alert popup akan muncul dengan data:
  ```
  {
    "method": "gps",              // Harus "gps"
    "statusTitle": "Siap Absen",  // Harus "Siap Absen"
    "isOnline": true,             // Harus true
    "locationActive": true,       // Harus true
    "hasLocation": true,          // Harus true
    "lat": "-6.xxx",              // Harus ada nilai
    "lng": "106.xxx",             // Harus ada nilai
    "hasSelfie": false,           // Harus false untuk GPS mode
    "hasQr": false                // Harus false untuk GPS mode
  }
  - Catat nilai-nilai ini
  - Screenshot debug alert

### Step 4: Lihat Console Logs
Cari di console logs:
- `[DEBUG] submitAttendance:` → Cek data yang dikirim
- `[DEBUG] ensureLocation passed:` → Location berhasil diambil
- `[DEBUG] GPS validation passed` → Di submit
- `[DEBUG] Response:` → Response dari server

Contoh console log yang benar:
```
[DEBUG] submitAttendance: {method: 'gps', isOnline: true, locationActive: true, hasLocation: true, lat: '-6.xxx', lng: '106.xxx', hasSelfie: false, qrDataVal: '', enabledModes: ['gps', 'qr']}
[DEBUG] ensureLocation passed: {lat: '-6.xxx', lon: '106.xxx', accuracy: '30.5', deviceTime: '2026-01-25T16:...'}
[DEBUG] Appended GPS data: {lat: '-6.xxx', lng: '106.xxx'}
[DEBUG] Submitting to /api/attendance/checkin
[DEBUG] Response: {ok: true, data: {...}, message: 'Presensi tercatat.', status: 200}
```

### Step 5: Lihat Terminal Logs (Backend)
Di terminal PowerShell dimana Flask running, cari:
```
[CHECKIN] User: arief@gmail.com, Method: gps
[CHECKIN] Location: lat=-6.xxx, lng=106.xxx
[CHECKIN] Policy: allow_gps=1, allow_qr=1, require_selfie=0
[CHECKIN] Selfie: NO, QR: NO
[CHECKIN] GPS validation passed: -6.xxx, 106.xxx
```

---

## Error Messages & Solutions

### Error: "Lokasi GPS wajib diisi"
**Penyebab:** 
- Location belum diambil
- Browser belum grant GPS permission
- GPS disabled

**Solusi:**
1. Klik location button (harus hijau)
2. Tunggu sampai ada koordinat
3. Allow browser permission untuk akses GPS

### Error: "Lokasi di luar radius site"
**Penyebab:** 
- Lokasi user tidak sesuai site configuration
- Site radius terlalu kecil

**Solusi:**
1. Periksa konfigurasi site (admin panel)
2. Cek center lat/lng dan radius
3. Test dari lokasi yang sesuai

### Error: "Selfie wajib untuk presensi"
**Penyebab:** 
- Dipilih method GPS+Selfie tapi selfie tidak diambil
- Policy require_selfie=1

**Solusi:**
1. Jika hanya GPS: pilih metode GPS (bukan GPS+Selfie)
2. Jika GPS+Selfie: ambil selfie dulu

### Alert Muncul Tapi Tidak Ada Toast
**Penyebab:**
- Response dari server error
- Toast container tidak terlihat

**Solusi:**
1. Scroll down untuk lihat toast notification
2. Lihat console untuk error detail
3. Check server logs

---

## Data yang Perlu Dikumpulkan untuk Debug

Jika error masih terjadi, kumpulkan:

1. **Screenshot debug alert** dengan semua nilai
2. **Console logs** yang dimulai dengan [DEBUG]
3. **Terminal output** yang dimulai dengan [CHECKIN]
4. **Settings yang sudah di-set:**
   - Policy: selfie=0 atau 1?
   - Brand/Client: GPS=1?
   - Dashboard: metode apa yang dipilih?
5. **Kondisi:**
   - Shift malam atau siang?
   - Status "Siap Absen" atau "Belum siap"?

---

## Expected Flow untuk GPS Mode

```
Frontend:
1. User klik Location button
   → latEl & lonEl terisi koordinat
   → updatePresenceReadiness() called
   → Status jadi "Siap Absen"

2. User klik Masuk
   → handleAttendance() trigger
   → Debug alert muncul
   → submitAttendance() called

3. submitAttendance():
   → method = "gps" ✓
   → Call ensureLocation()
   → Get lat, lng, accuracy, device_time ✓
   → FormData append: method, lat, lng, accuracy, device_time ✓
   → POST /api/attendance/checkin

Backend:
1. attendance_checkin() called
   → Log: [CHECKIN] User, Method
   → Load policy
   → Validate method allowed
   → Validate location (not empty, valid, within radius) ✓
   → Skip selfie validation (method != gps_selfie) ✓
   → Skip QR validation (method != qr) ✓
   → Create record
   → Return: ok=true

Frontend:
4. Response received
   → showToast("success", "Presensi tercatat.")
   → Update status label
   → updatePresenceReadiness()

DONE ✓
```

Pastikan setiap step berhasil!
