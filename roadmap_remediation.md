# Roadmap Remediation

## Phase 0 — Blocker (0.5–1.5 hari)
- [x] Wajibkan `FLASK_SECRET` dan fail fast (prod only); hapus fallback secret.
- [x] Hapus/gate seed user + default password (env flag).
- [x] Keluarkan `app.db` / `presensi.db` dari repo + `.gitignore`.

## Phase 1 — Security kritikal (1–3 hari)
- [ ] CSRF untuk semua POST state-changing + ubah logout ke POST.
- [ ] Validasi `is_active` di setiap request / revoke session.
- [ ] Implement reset password real (token time-bound/OTP).
- [ ] QR signing + expiry (HMAC/secret per tenant).

## Phase 2 — Data integrity (2–5 hari)
- [ ] Transaksi atomik untuk approval manual attendance + re-check status.
- [ ] Enforcement 1 check-in/checkout per hari (constraint + logika).
- [ ] Unique constraints `email` / `nik` / `no_hp`, migrasi & dedup data.
- [ ] Foreign keys inti + cleanup orphan.

## Phase 3 — Workflow & policy alignment (1–3 hari)
- [ ] Samakan policy manual attendance antara UI/API.
- [ ] Perbaiki rule approval scope-based (assignment).
- [ ] Batasi akses leave pending sesuai role approver.

## Phase 4 — Hygiene & UX (0.5–1 hari)
- [ ] Simpan path selfie ke DB atau hentikan penyimpanan.
- [ ] Hapus dead code `_role_from_email`.
- [ ] Ganti asset demo + perbaiki copy admin overview.
