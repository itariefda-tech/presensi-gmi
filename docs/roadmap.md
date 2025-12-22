
---

# 🗺️ `ROADMAP.md` (Checklist sampai Final)

```md
# HRIS GMI — Development Roadmap

## PHASE 1 — FOUNDATION
- [x] Login system & role demo
- [x] Dashboard admin (overview, clients, employees)
- [x] Dashboard pegawai (basic placeholder)

---

## PHASE 2 — ATTENDANCE CORE
- [x] Struktur data attendance (DEMO_ATTENDANCE)
- [x] Endpoint check-in (GPS + selfie, multipart)
- [x] Endpoint check-out (GPS + selfie, multipart)
- [x] Signup selfie upload (multipart)
- [x] Simpan selfie ke static/uploads
- [x] Foto profil di dashboard (dari selfie signup)
- [x] Validasi GPS radius (100m)
- [x] Upload selfie (multipart file)
- [x] Presensi GPS-only fallback

---

## PHASE 3 — QR / BARCODE SCAN
- [x] Camera access (getUserMedia)
- [x] QR scan via camera (jsQR atau setara)
- [x] Validasi hasil scan
- [x] Integrasi QR ke attendance method
- [x] Error handling device tidak support kamera

---

## PHASE 4 — MANUAL ATTENDANCE (DARURAT)
- [x] Form manual attendance (Supervisor/Koordinator)
- [x] Alasan wajib
- [x] Status pending
- [x] List manual attendance pending
- [x] Approval manual attendance
- [x] Supervisor prioritas
- [x] Koordinator fallback

---

## PHASE 5 — LEAVE MANAGEMENT
- [x] Struktur data leave (DEMO_LEAVE_REQUESTS)
- [x] Form izin/sakit/absen (pegawai)
- [x] Endpoint leave request
- [x] Riwayat leave pegawai
- [x] Endpoint pending leave
- [x] Approval leave
- [x] Supervisor → Koordinator fallback

---

## PHASE 6 — DASHBOARD APPROVAL
- [x] Halaman Approvals (Admin/Supervisor)
- [x] Tab Leave Requests
- [x] Tab Manual Attendance
- [x] Action approve / reject
- [x] Catatan approval

---

## PHASE 7 — UX & STABILITY
- [ ] Toast / notification dashboard
- [ ] Validasi form client-side
- [ ] Error handling fetch API
- [ ] Mobile-friendly dashboard pegawai

---

## PHASE 8 — FINAL DEMO READY
- [ ] Role access tested satu per satu
- [ ] Login & slider dipastikan tidak berubah
- [ ] Tidak ada error JS console
- [ ] Semua flow utama berjalan
- [ ] README & ROADMAP final

---

## PHASE 9 — NEXT LEVEL (POST DEMO)
- [ ] Migrasi ke SQLite / MySQL
- [ ] Audit trail detail
- [ ] Attachment file storage real
- [ ] Multi lokasi & shift
- [ ] Hardening security
