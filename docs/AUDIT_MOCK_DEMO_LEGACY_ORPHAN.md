# Audit Mock/Demo/Legacy/Orphan

Audit ini merangkum temuan status mock, demo, label legacy, dan orphan di repo saat ini. Fokus pada jejak implementasi (code/templating) dan implikasi operasional.

Tanggal audit: 2026-01-08

---

## Ringkasan Cepat

- Presensi (checkin/checkout) dan leave sudah pindah ke SQLite (tidak in-memory).
- Label "Mock" masih muncul pada laporan harian pegawai.
- Legacy data masih disimpan (`client_name`, `employee_site`).
- Orphan site masih terdeteksi di UI admin (site tanpa client valid).
- Teks "demo" masih muncul di beberapa pesan auth/QR.

---

## 1) Demo (Label/Teks)

### Pesan auth/QR
- Beberapa pesan masih memakai label "demo" (signup/reset/login, dan validasi QR).

Referensi:
- `app.py`

### README
- README sudah diperbarui (tidak lagi menonjolkan status demo).

---

## 2) Mock (UI/UX)

- Laporan harian pegawai masih berlabel "Mock" dan data statis.

Referensi:
- `templates/dashboard/employee.html` (section "Laporan Harian (Mock)").

---

## 3) Legacy (Kode/Data/Label)

### Legacy data fields & relasi
- `sites.client_name` masih disimpan untuk kompatibilitas.
- `employee_site` masih ada sebagai relasi legacy.

Referensi:
- `docs/client_entity.md` (status legacy).
- `register_issue.md` (catatan legacy client_name/employee_site).

### Legacy endpoints
- `/api/attendance/manual`, `/api/attendance/pending`, `/api/attendance/approve`
  tetap ada untuk kompatibilitas API, tetapi sudah menggunakan SQLite.

Referensi:
- `app.py` (endpoint legacy manual attendance).

### Label "Legacy" di UI
- "PIC Legacy" di client profile menandai PIC lama sebelum multi-PIC.

Referensi:
- `templates/dashboard/admin_client_profile.html`

---

## 4) Orphan (Data/Label/UI)

### Orphan site
- `sites` yang punya `client_id` invalid diberi flag `is_orphan`.
- Admin Sites menampilkan badge "Orphan" dan blok "Audit: Site tanpa client".

Referensi:
- `app.py` (`_list_sites` memberi `is_orphan`).
- `templates/dashboard/admin_sites.html` (badge Orphan dan audit block).

### Catatan tambahan
- `docs/roadmap.md` menyebut "Audit: no orphan sites", namun UI masih menampilkan audit orphan.
  Perlu verifikasi data aktual di DB untuk memastikan status benar-benar bersih.

---

## 5) Risiko & Dampak

- Mock report menurunkan persepsi "production-ready".
- Legacy `client_name` berpotensi drift saat rename client.
- Orphan site menunjukkan integritas relasi belum sepenuhnya bersih.
- Label "demo" tersisa bisa menimbulkan kebingungan status readiness.

---

## 6) Saran Tindak Lanjut

- Ganti "Laporan Harian (Mock)" ke data real atau label jelas "Coming Soon".
- Rencana cleanup `client_name` dan `employee_site` setelah verifikasi migrasi assignment.
- Jalankan audit data untuk memastikan tidak ada orphan site di DB.
- Konsolidasikan label "demo" di pesan auth/QR sesuai status terkini.
