# 🧱 TECH STACK — HRIS GMI

Dokumen ini adalah sumber kebenaran (source of truth) untuk semua teknologi yang digunakan dalam project HRIS GMI.

Tujuan:
- Menjaga konsistensi antar agent & developer
- Menghindari stack campur aduk
- Menjadi referensi saat scaling ke enterprise

---

## 🧩 CORE STACK

### Backend
- Python 3.x
- Flask (monolith modular)
- SQLite (current) → target: PostgreSQL (production)

Catatan:
- Saat ini masih menggunakan struktur sederhana (app.py)
- Sudah mulai mengarah ke modular via blueprint

---

### Frontend
- HTML (Jinja2 templating)
- CSS custom (tanpa framework)
- Vanilla JavaScript (tanpa framework)

Referensi:
- app.js → auth & UI logic
- dashboard_employee.js → presensi
- dashboard_admin.js → approval

---

### UI System
- Theme system menggunakan:
  - `data-theme`
  - localStorage persistence

- 2 theme aktif:
  - dark (default)
  - light

Target:
- Multi-theme (Ocean, Sunset, Forest, dll)

---

### Mobile Strategy
- Mobile-first (employee dashboard)
- Desktop-first (admin dashboard)

Teknologi:
- Responsive CSS
- Swipe UI (mobile JS)
- Kamera & GPS API (browser)

---

## 📡 API DESIGN

### Style
- REST-like (JSON)
- Endpoint berbasis role

Contoh:
- `/api/auth/login`
- `/api/attendance/checkin`
- `/api/attendance/approve`

---

### Validasi
- Client-side (JS)
- Server-side (Flask)

---

### Security (Current)
- Session-based auth
- Basic validation

⚠️ BELUM ADA:
- JWT
- RBAC granular
- Rate limit
- Audit log proper

---

## 🗃️ DATA LAYER

### Current
- SQLite
- In-memory structure:
  - DEMO_ATTENDANCE
  - DEMO_USERS

### Target (Enterprise)
- PostgreSQL
- Multi-tenant structure:
  - clients
  - sites
  - employees
  - attendance
  - leave
  - addons

---

## 📦 FILE STORAGE

- Selfie:
  - `/static/uploads/selfies`
- Attendance:
  - `/static/uploads/attendance`

Limit:
- Max 2MB per file

---

## ⚙️ ARCHITECTURE TARGET

### Current
Monolith:
app.py
templates/
static/


### Target (Phase Enterprise)

app/
├── modules/
│ ├── auth/
│ ├── attendance/
│ ├── leave/
│ ├── client/
│ └── addon/
├── core/
│ ├── database/
│ ├── security/
│ └── utils/
├── api/
└── services/


---

## 🧠 DESIGN PRINCIPLES

1. **Mobile-first reality**
   → pegawai di lapangan, bukan di kantor

2. **Offline tolerance**
   → jaringan tidak stabil

3. **Multi-role system**
   → employee, supervisor, koordinator, admin

4. **Fallback system wajib**
   → GPS gagal → manual attendance

5. **Audit trail penting**
   → semua harus bisa ditelusuri

---

## 🚀 SCALING STRATEGY

### Short Term
- Stabilkan fitur core (attendance, leave)
- Rapikan API

### Mid Term
- Modularisasi (addon system)
- Role-based access lebih ketat

### Long Term
- SaaS HRIS
- Multi-client + multi-site
- Plugin / addon marketplace

---

## ⚠️ RULES (WAJIB)

- ❌ Jangan tambah framework frontend (React/Vue) tanpa keputusan arsitektur
- ❌ Jangan ubah struktur API tanpa update dokumentasi
- ❌ Jangan hardcode logic client-specific

- ✅ Semua perubahan harus backward-compatible
- ✅ Semua fitur baru harus modular

---

## 🧭 FINAL NOTE

Stack ini sengaja:
- ringan
- fleksibel
- cepat dikembangkan

Bukan untuk gaya.
Tapi untuk bertahan di dunia nyata (outsource, lapangan, chaos).
