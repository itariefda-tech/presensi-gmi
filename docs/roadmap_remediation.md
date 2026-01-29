# Roadmap Remediation

## Phase 0 — Blocker (0.5–1.5 hari)
- [ ] (rollback) Wajibkan `FLASK_SECRET` dan fail fast (prod only); hapus fallback secret.
- [ ] (rollback) Hapus/gate seed user + default password (env flag).
- [x] Keluarkan `app.db` / `presensi.db` dari repo + `.gitignore`.

## Phase 1 - Security kritikal (1-3 hari)
- [x] CSRF untuk semua POST state-changing + ubah logout ke POST.
- [x] Validasi `is_active` di setiap request / revoke session.
- [x] Implement reset password real (token time-bound/OTP).
- [x] QR signing + expiry (HMAC/secret per tenant).

## Phase 2 - Data integrity (2-5 hari)
- [x] Transaksi atomik untuk approval manual attendance + re-check status.
- [x] Enforcement 1 check-in/checkout per hari (constraint + logika).
- [x] Unique constraints `email` / `nik` / `no_hp`, migrasi & dedup data.
- [x] Foreign keys inti + cleanup orphan.

## Phase 3 - Workflow & policy alignment (1-3 hari)
- [x] Samakan policy manual attendance antara UI/API.
- [x] Perbaiki rule approval scope-based (assignment).
- [x] Batasi akses leave pending sesuai role approver.

## Phase 4 - Hygiene & UX (0.5-1 hari)
- [x] Simpan path selfie ke DB atau hentikan penyimpanan.
- [x] Hapus dead code `_role_from_email`.
- [x] Ganti asset demo + perbaiki copy admin overview.
