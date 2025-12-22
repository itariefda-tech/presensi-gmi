# HRIS GMI — Attendance & Leave System (Tanpa Payroll)

HRIS GMI adalah aplikasi Human Resource Information System ringan yang berfokus pada:
- Presensi (Attendance)
- Izin / Sakit / Absen
- Approval berjenjang (Supervisor → Koordinator)

Payroll sengaja TIDAK termasuk scope.

Aplikasi ini dirancang untuk kondisi lapangan nyata:
- Sinyal tidak stabil
- Pegawai mobile
- Supervisi bertingkat
- Audit trail jelas

---

## 🎯 Tujuan Sistem
1. Mencatat kehadiran pegawai secara akurat dan fleksibel
2. Menyediakan metode presensi modern tanpa alat tambahan
3. Memberikan jalur darurat (manual attendance) yang tetap terkontrol
4. Mengelola izin/sakit/absen dengan alur persetujuan yang realistis
5. Menjadi pondasi HRIS lanjutan (enterprise-ready)

---

## 🧩 Scope Fitur

### 1️⃣ Attendance / Presensi

#### Metode Presensi
- **GPS + Selfie** (utama)
- **GPS saja** (fallback)
- **Barcode / QR Code via Camera Scan**
- **Manual Attendance** oleh Supervisor / Koordinator (kondisi darurat)

#### Aturan GPS
- Radius minimal **100 meter** (default)
- Validasi dilakukan client-side & server-side (basic)
- Tidak menggunakan anti-mock GPS (tahap lanjut)

#### Manual Attendance
- Hanya bisa dilakukan oleh:
  - Supervisor
  - Koordinator
- Status awal: **pending**
- Alasan wajib diisi
- Tidak langsung final

#### Final Approval Attendance
- Manual attendance **harus di-approve**
- Alur:
  1. Supervisor (prioritas)
  2. Jika tidak ada respon → Koordinator
- Cukup satu approval (final)

---

### 2️⃣ Izin / Sakit / Absen (Leave Management)

#### Dashboard Pegawai
Pegawai dapat mengajukan:
- Izin
- Sakit
- Absen tidak masuk

Field:
- Tipe pengajuan
- Tanggal (from – to)
- Alasan (wajib)
- Lampiran (opsional)

Status:
- `pending`
- `approved`
- `rejected`

Pegawai dapat melihat riwayat pengajuannya sendiri.

#### Approval Leave
- Approver:
  1. Supervisor (utama)
  2. Koordinator (fallback)
- Salah satu approval sudah cukup
- Disimpan:
  - siapa yang approve
  - waktu approval
  - catatan

---

## 👥 Role & Hak Akses

| Role         | Hak Akses Utama |
|--------------|-----------------|
| employee     | Presensi, ajukan izin, lihat data sendiri |
| supervisor   | Approve izin & manual attendance |
| koordinator  | Approve izin & manual attendance (fallback) |
| client_admin | Monitoring client |
| admin        | Monitoring global |

Akses endpoint dicek via session & role.
Akses tidak sah → `403 Forbidden`.

---

## 🔌 API Endpoint (Target)

### Attendance
- `POST /api/attendance/checkin`
- `POST /api/attendance/manual`
- `GET  /api/attendance/pending`
- `POST /api/attendance/approve`

### Leave
- `POST /api/leave/request`
- `GET  /api/leave/my`
- `GET  /api/leave/pending`
- `POST /api/leave/approve`

---

## 🗂 Data Storage (Tahap Demo)
- Menggunakan in-memory storage:
  - `DEMO_ATTENDANCE = []`
  - `DEMO_LEAVE_REQUESTS = []`
- Tidak bercampur dengan auth demo
- Siap dimigrasikan ke DB (SQLite / MySQL)

---

## 🎨 UI / UX Rules (WAJIB)
1. **TIDAK BOLEH mengubah**:
   - Tampilan login
   - Slider login / signup / forgot
   - CSS dan JS login
2. Fitur baru hanya di:
   - Dashboard Pegawai
   - Dashboard Admin / Supervisor
3. Penamaan class, id, route harus konsisten dan tidak bentrok
4. Style mengikuti `dashboard.css`

---

## 🚀 Cara Menjalankan (Dev)

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py

Akses:

http://localhost:5020/

🧪 Demo Login :
    Admin:
        email: hr@gmi.com
        password: hr123456
        Role lain:
        email mengandung employee, supervisor, koordinator, client


    Pegawai untuk masuk dashboard pegawai :
        email: arief@gmail.com
        password: arief123

---