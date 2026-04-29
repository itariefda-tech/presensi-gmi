# 🏗️ SYSTEM ARCHITECTURE — HRIS GMI

Dokumen ini mendefinisikan arsitektur sistem secara menyeluruh.

Tujuan:
- Menjadi blueprint utama
- Mencegah refactor brutal di masa depan
- Menjaga arah menuju HRIS enterprise

---

## 🧠 ARSITEKTUR SAAT INI (REALITA)

Model:
- Monolith Flask

Struktur:
- app.py (single entry point)
- templates (Jinja)
- static (CSS, JS)

Karakter:
- Cepat dikembangkan
- Minim layer
- Belum scalable

---

## 🎯 TARGET ARSITEKTUR (ENTERPRISE READY)

Model:
> Modular Monolith → Microservices (opsional di masa depan)

Kenapa tidak langsung microservices?
- Overkill
- Kompleks
- Belum butuh

---

## 🧱 STRUKTUR FINAL (TARGET)


app/
├── modules/
│ ├── auth/
│ │ ├── routes.py
│ │ ├── service.py
│ │ └── schema.py
│ │
│ ├── attendance/
│ ├── leave/
│ ├── client/
│ ├── employee/
│ └── addon/
│
├── core/
│ ├── db.py
│ ├── security.py
│ ├── config.py
│ └── utils.py
│
├── api/
│ └── router.py
│
├── web/
│ └── views.py
│
└── main.py


---

## 🔁 FLOW REQUEST

Client → API → Module → Service → Database

Contoh:

Frontend
↓
/api/attendance/checkin
↓
attendance.routes
↓
attendance.service
↓
database


---

## 🧩 LAYER EXPLANATION

### 1. ROUTES (Controller)
- Handle request
- Validasi basic
- Return response

❌ Tidak boleh ada business logic berat

---

### 2. SERVICE (Business Logic)
- Validasi utama
- Rule bisnis
- Decision making

✔ Semua logic inti di sini

---

### 3. SCHEMA
- Validasi input
- Struktur data

---

### 4. CORE
Shared system:
- DB connection
- Auth
- Utils

---

## 🧠 DOMAIN MODEL (WAJIB DIPAHAMI)

### Entity utama:

- Client
- Site
- Employee
- Attendance
- Leave
- Addon

---

## 🔗 RELATIONSHIP

Client
  └── Site
        └── Employee
              ├── Attendance
              └── Leave

---

## 🏢 MULTI-TENANT DESIGN

Rule:
- 1 client = 1 organisasi
- 1 client bisa punya banyak site
- 1 site punya aturan berbeda

⚠️ Semua query WAJIB scoped by client_id

---

## ⚙️ ADD-ON SYSTEM

Konsep:
- Feature tidak hardcoded
- Diaktifkan via addon

Contoh:

addons = ["attendance", "leave", "payroll_plus"]


Rule:
- Semua fitur cek:
  has_addon(client, "feature")

---

## 🔐 SECURITY LAYER

Current:
- Session-based

Target:
- JWT (optional)
- Role-based access
- Permission-based access

---

## 📡 API LAYER

- Semua API di `/api/*`
- Web view di `/dashboard/*`

---

## 📱 FRONTEND ARCHITECTURE

- Server-rendered (Jinja)
- Enhanced by JS

Rule:
- Jangan pindah ke SPA tanpa keputusan arsitektur

---

## 🧠 SCALING PATH

### Phase 1
- Monolith stabil

### Phase 2
- Modular monolith

### Phase 3
- Extract service (optional)
  - auth service
  - attendance service

---

## ⚠️ ANTI-PATTERN (DILARANG)

- ❌ Logic di template
- ❌ Query langsung di route
- ❌ Hardcode client
- ❌ Endpoint liar tanpa standar

---

## 🧭 FINAL NOTE

Arsitektur ini bukan untuk keren-kerenan.

Ini untuk:
- tahan banting
- mudah dikembangkan
- bisa dijual

Kalau dilanggar:
> kamu akan bayar mahal saat scale.