---

# ROADMAP.md (Checklist sampai Final)

```md
# HRIS GMI - Development Roadmap

## PHASE 1 - FOUNDATION
- [x] Login system & role demo
- [x] Dashboard admin (overview, clients, employees)
- [x] Dashboard pegawai (basic placeholder)

---

## PHASE 2 - ATTENDANCE CORE
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

## PHASE 3 - QR / BARCODE SCAN
- [x] Camera access (getUserMedia)
- [x] QR scan via camera (jsQR atau setara)
- [x] Validasi hasil scan
- [x] Integrasi QR ke attendance method
- [x] Error handling device tidak support kamera

---

## PHASE 4 - MANUAL ATTENDANCE (DARURAT)
- [x] Form manual attendance (Supervisor/Manager Operasional)
- [x] Alasan wajib
- [x] Status pending
- [x] List manual attendance pending
- [x] Approval manual attendance
- [x] Supervisor prioritas
- [x] Manager Operasional fallback

---

## PHASE 5 - LEAVE MANAGEMENT
- [x] Struktur data leave (DEMO_LEAVE_REQUESTS)
- [x] Form izin/sakit/absen (pegawai)
- [x] Endpoint leave request
- [x] Riwayat leave pegawai
- [x] Endpoint pending leave
- [x] Approval leave
- [x] Supervisor -> Manager Operasional fallback

---

## PHASE 6 - DASHBOARD APPROVAL
- [x] Halaman Approvals (Admin/Supervisor)
- [x] Tab Leave Requests
- [x] Tab Manual Attendance
- [x] Action approve / reject
- [x] Catatan approval

---

## PHASE 7 - UX & STABILITY
- [x] Toast / notification dashboard
- [x] Validasi form client-side
- [x] Error handling fetch API
- [x] Mobile-friendly dashboard pegawai

---

## PHASE 8 - FINAL DEMO READY
- [x] Role access tested satu per satu (pending: setting/konfigurasi role)
- [x] Login & slider dipastikan tidak berubah
- [x] Tidak ada error JS console
- [x] Semua flow utama berjalan
- [x] README & ROADMAP final

---

## PHASE 9 - POST ENTITY (DEFERRED)
- Catatan: Phase 9 ditunda sampai Phase 12-15 selesai.
- [x] Attachment file storage real
- [x] Hardening security

---

============================================================
PHASE 10 - CLIENT & SITE RELATION HARDENING (ENTERPRISE BASE)
============================================================
Goal:
- Data integrity kuat
- Client -> Site pakai FK, bukan string
- Pondasi siap untuk assignment + policy

Checklist:
- [x] Add column sites.client_id (FK -> clients.id)
- [x] Data migration: sites.client_name -> sites.client_id
- [x] Stop relying on client_name for relational logic (keep only as legacy/display if needed)
- [x] Add updated_at to clients + sites
- [x] Add unique rule to prevent duplicate client identity (name or legal_name)
- [x] Audit: no orphan sites (site without valid client_id)
- [x] Update queries/UI to join by client_id

Outcome:
- Rename client aman
- Relasi Client-Site stabil
- Siap naik ke Assignment

------------------------------------------------------------

=========================================
PHASE 11 - ASSIGNMENT ENGINE (OUTSOURCING)
=========================================
Goal:
- Penempatan pegawai real: Employee -> Site (period-based)
- Dashboard pegawai bisa tampilkan Client + Site aktif
- Validasi presensi berbasis penempatan

Checklist:
- [x] Create assignments table (employee_user_id, site_id, start_date, end_date, status, job_title)
- [x] Migration: employee_site/supervisor_sites -> assignment ACTIVE (as needed)
- [x] Rule: limit 1 ACTIVE assignment per employee (default) OR define multi-site policy
- [x] Employee dashboard: show active Client + Site (from ACTIVE assignment)
- [x] Server validation: checkin/checkout must match active assignment site
- [x] Assignment timeline: keep history (ENDED assignments)
- [x] Admin UI: simple assignment management (assign/unassign)

Outcome:
- "Pegawai kerja untuk siapa & di mana" jadi fakta sistem
- Presensi tidak bisa asal lokasi

------------------------------------------------------------

==============================================
PHASE 12 - ATTENDANCE POLICY ENGINE (CUSTOMIZE)
==============================================
Goal:
- Tiap client/site bisa punya aturan presensi sendiri
- Policy inheritance: Client default -> Site override -> System fallback

Checklist:
- [x] Create attendance_policies table
- [x] Policy scope: CLIENT (default) and SITE (override)
- [x] Add effective dating: effective_from, effective_to
- [x] Minimal rule fields:
      - work_duration_minutes
      - grace_minutes
      - late_threshold_minutes
      - require_selfie (0/1)
      - allow_gps (0/1)
      - allow_qr (0/1)
      - auto_checkout (0/1)
      - cutoff_time
- [x] Implement policy resolver:
      1) active site policy
      2) active client policy
      3) system defaults
- [x] Integrate policy into checkin/checkout server validation
- [x] Admin UI: Policy tab under Client (and optional Site override UI)

Outcome:
- Klaim "custom per client" menjadi real
- Sistem terasa enterprise-ready

------------------------------------------------------------

=================================================
PHASE 13 - CLIENT PROFILE & ADMIN UX UPGRADE (PRO)
=================================================
Goal:
- Client page terasa HRIS mahal: tabbed profile, multi-PIC, ringkasan operasional

Checklist:
- [x] Client profile tabs:
      - Overview
      - Sites
      - Assignments (summary)
      - Policies
      - Contacts (PIC)
- [x] Create client_contacts (multi-PIC: operational/billing/HR/other)
- [x] Mark primary PIC per type
- [x] Add basic SLA/compliance summary (optional)

Outcome:
- Admin view "Client" sebagai akun enterprise, bukan sekedar row tabel

------------------------------------------------------------

===============================================
PHASE 14 - OPERATIONAL INTELLIGENCE (VALUE ADD)
===============================================
Goal:
- Insight untuk HR/ops: bukan cuma data mentah
- Warning untuk gap operasional

Checklist:
- [x] Dashboard summary per client:
      - late count
      - absent count
      - leave pending count
- [x] Compliance indicator per site (simple scoring)
- [x] Alerts:
      - site without policy
      - employee without active assignment
      - assignment expired
- [x] Lightweight audit log for policy/assignment changes
- [x] Audit trail detail (extended)

Outcome:
- HR dapat "signal", bukan sekadar laporan

------------------------------------------------------------

==================================================
PHASE 15 - CONTRACT, SLA & BILLING READINESS (OPT)
==================================================
Goal:
- Siap untuk client besar & komersialisasi bertahap

Checklist:
- [ ] Add client_contracts minimal fields:
      - contract_no
      - start_date / end_date
      - notice_period_days
      - scope_summary
      - sla_summary
- [ ] Billing schema (optional):
      - billing_type (PER_HEAD / PER_SITE / PER_SHIFT)
      - rate
      - tax_percent
      - payment_terms_days
      - invoice_email
- [ ] Read-only recap: attendance -> billing summary (optional)

Outcome:
- Produk siap naik kelas untuk enterprise

------------------------------------------------------------

=========================================
PHASE 16 - HARDENING & SCALE (POST ENTER)
=========================================
Goal:
- Ketahanan sistem, siap scale, minim demo logic

Checklist:
- [x] Migrasi storage attendance + leave ke DB:
      - [x] hilangkan in-memory demo
      - [ ] (opsional) switch engine ke MySQL saat infra siap
- [ ] Permission matrix more granular (RBAC + per-client scope)
- [ ] Soft delete + retention policy
- [ ] Indexing + performance tuning
- [ ] Final docs: ERD + API spec + migration notes

Outcome:
- Stabil, scalable, audit-ready
============================================================
