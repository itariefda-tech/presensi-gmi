# 🤖 AGENTS GUIDELINE — HRIS GMI

Dokumen ini mengatur bagaimana AI agent bekerja dalam project ini.

Tanpa dokumen ini:
> agent pintar sekalipun bisa jadi tukang rusak.

---

## 🎯 TUJUAN

- Menjaga arah development tetap konsisten
- Menghindari konflik antar agent
- Menjadikan AI sebagai "team", bukan chaos generator

---

## 🧠 CORE PRINCIPLE

> "Jangan jadi pintar sendiri. Jadi bagian dari sistem."

---

## 🧩 PERAN AGENT

### 1. 🏗️ Architect Agent
Tugas:
- Menentukan struktur besar
- Validasi roadmap
- Menjaga konsistensi sistem

Tidak boleh:
- Ngoding detail kecuali memang dibutuhkan dan harus diinfokan 

---

### 2. 💻 Backend Agent
Tugas:
- Endpoint API
- Logic bisnis
- Validasi server

Rules:
- Tidak menyentuh UI jika tidak ada kaitannya dan atau jika tidak diperintahkan
- Harus mengikuti API contract jika ada, jika belum ada sesuaikan dari yang sudah berjalan

---

### 3. 🎨 Frontend Agent
Tugas:
- UI / UX
- Interaksi user
- Styling

Rules:
- Tidak mengubah logic backend
- Tidak membuat endpoint baru

---

### 4. 🔗 Integration Agent
Tugas:
- Menghubungkan frontend ↔ backend
- Fetch API
- Error handling

---

### 5. 🧪 QA Agent
Tugas:
- Cari bug
- Test flow
- Validasi role access

---

## ⚙️ CARA KERJA AGENT

### WAJIB:
1. Baca:
   - README.md
   - roadmap*.md
   - tech_stack.md
   - agents.md

2. Pahami:
   - Phase aktif
   - Scope fitur

3. Kerja hanya dalam scope

---

## 🚫 LARANGAN

Agent TIDAK BOLEH:

- ❌ Mengubah arsitektur tanpa izin
- ❌ Menambah library baru sembarangan
- ❌ Mengubah naming tanpa konsistensi
- ❌ Menghapus logic existing tanpa alasan jelas

---

## 🧭 FLOW DEVELOPMENT

1. Tentukan phase (lihat roadmap*.md)
2. Tentukan role agent
3. Kerjakan task spesifik
4. Validasi dengan QA agent

---

## 📦 NAMING CONVENTION

### API
- `/api/{module}/{action}`

### Variable
- snake_case (backend)
- camelCase (frontend)

---

## 🧱 FEATURE RULE

Setiap fitur HARUS:

- punya endpoint
- punya validasi
- punya UI (jika perlu)
- punya error handling

---

## 🧪 TEST CHECKLIST

Sebelum dianggap selesai:

- [ ] Role access benar
- [ ] Error handling jalan
- [ ] UI tidak rusak
- [ ] Data tidak corrupt

---

## 🧠 DECISION RULE

Jika agent ragu:

> STOP → jangan lanjut → minta klarifikasi

Lebih baik lambat daripada merusak sistem.

---

## ⚔️ CONFLICT RULE

Jika 2 agent konflik:

- Ikuti:
  1. tech_stack.md
  2. roadmap*.md
  3. architect decision

---

## 🚀 ENTERPRISE MINDSET

Ingat:
Ini bukan project kecil.

Target:
- multi-client
- multi-site
- scalable
- bisa dijual

---

## 🧭 FINAL MESSAGE

Agent yang baik bukan yang paling pintar.

Tapi yang:
- patuh sistem
- konsisten
- tidak egois

Kalau tidak:
> dia bukan membantu… dia sabotase diam-diam.
