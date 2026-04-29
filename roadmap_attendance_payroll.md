# Roadmap Attendance & Payroll Integration

## 1. Objective

Roadmap ini menjadi panduan perbaikan integrasi:

- Attendance / Absence
- Attendance Policy
- Payroll berbasis Policy
- Sinkronisasi Employee, Client Admin, dan Admin / Superadmin Dashboard

Target akhir:

- Attendance menjadi single source of truth untuk payroll.
- Payroll selalu memakai policy yang benar: `payroll_scheme` dan `payroll_schedule`.
- Semua dashboard membaca data dengan definisi periode dan scope yang sama.
- Tidak ada hardcoded period, double penalty, atau logic attendance yang saling berbeda.

## 2. Scope

### In Scope

- Attendance check-in / check-out.
- Manual attendance yang sudah approved.
- Attendance summary.
- Attendance policy.
- Payroll generation, payroll list, payroll detail, approval.
- Filter dashboard yang berkaitan dengan attendance dan payroll.

### Out of Scope

- Patrol / Guard Tour.
- User management.
- Leave selain yang sudah dipakai sebagai komponen attendance summary.
- Modul AI analysis.
- Refactor besar arsitektur di luar file dan helper yang dibutuhkan.

## 3. Current Verified State

### Sudah Ada

- Policy resolver: `SITE -> CLIENT -> GLOBAL -> default`.
- `payroll_scheme`:
  - `PRORATED_ATTENDANCE`
  - `FULL_MONTHLY_DEDUCTION`
- `payroll_schedule`:
  - `MONTH_END`
  - `MID_MONTH`
- Payroll sudah menyimpan:
  - `period_start`
  - `period_end`
  - `pay_date`
  - `payroll_scheme`
  - `payroll_schedule`
  - `client_id`
  - `site_id`
  - `employee_id`
- Payroll approved sudah sebagian immutable: tidak bisa regenerate/update adjustment.

### Masih Bermasalah

- Employee attendance summary masih berbasis calendar month.
- Client attendance report/export masih berbasis calendar month.
- Client Admin payroll scope masih terlalu site-level, belum tenant-wide.
- Naming `branch_id` dan `site_id` masih bercampur.
- Dashboard belum konsisten menampilkan `payroll_scheme`.
- Beberapa UI default period masih current month, bukan current pay cycle.

## 4. Standard Terms

### Attendance Domain

| Term | Definisi |
| --- | --- |
| `attendance_record` | Satu data check-in atau check-out. |
| `attendance_day` | Satu hari yang punya check-in valid. |
| `attendance_summary` | Agregasi attendance dalam satu pay cycle. |
| `working_days` | Hari kerja aktif berdasarkan assignment dalam pay cycle. |
| `late_days` | Jumlah hari check-in melewati aturan policy/shift. |
| `absent_days` | `working_days - attendance_days - leave_days`. |
| `leave_days` | Hari leave approved dalam pay cycle. |

### Payroll Domain

| Term | Definisi |
| --- | --- |
| `salary_base` | Gaji pokok periode penuh. |
| `daily_rate` | `salary_base / working_days`. |
| `gross_salary` | Nilai gaji sebelum potongan lain. |
| `net_salary` | Nilai final setelah potongan dan tunjangan. |
| `payroll_record` | Snapshot payroll per employee dan period. |

### Policy Domain

| Field | Value |
| --- | --- |
| `payroll_scheme` | `PRORATED_ATTENDANCE` / `FULL_MONTHLY_DEDUCTION` |
| `payroll_schedule` | `MONTH_END` / `MID_MONTH` |

## 5. Pay Cycle Standard

`pay_cycle` adalah kontrak pusat antara attendance dan payroll.

```json
{
  "period": "YYYY-MM",
  "period_start": "YYYY-MM-DD",
  "period_end": "YYYY-MM-DD",
  "pay_date": "YYYY-MM-DD",
  "payroll_scheme": "PRORATED_ATTENDANCE",
  "payroll_schedule": "MONTH_END"
}
```

### MONTH_END

Contoh period `2026-02`:

- `period_start`: `2026-02-01`
- `period_end`: `2026-02-28`
- `pay_date`: `2026-02-28` atau aturan existing `min(30, last_day)`

### MID_MONTH

Contoh period `2026-02`:

- `period_start`: `2026-01-16`
- `period_end`: `2026-02-15`
- `pay_date`: `2026-02-16`

## 6. Target End-to-End Flow

```text
Employee Dashboard
  -> Attendance Service
  -> Policy Resolver
  -> Pay Cycle Resolver
  -> Attendance Aggregator
  -> Payroll Calculator
  -> Payroll Snapshot
  -> Client Admin Dashboard
  -> Admin / Superadmin Dashboard
```

## 7. Implementation Roadmap

### Phase 1: Core Resolver & Aggregator

Status: Completed for backend helper and payroll usage.

Bisa dikerjakan paralel dengan Phase 4 bagian UI read-only.

Tasks:

- [x] Buat shared helper `resolve_pay_cycle(...)`.
- [x] Helper harus memakai resolver policy existing: `SITE -> CLIENT -> GLOBAL -> default`.
- [x] Helper harus mengembalikan `period_start`, `period_end`, `pay_date`, `payroll_scheme`, `payroll_schedule`.
- [x] Buat shared helper `calculate_attendance_summary_by_cycle(...)`.
- [x] Attendance summary harus menghitung:
  - `working_days`
  - `attendance_days`
  - `late_days`
  - `absent_days`
  - `leave_days`
- [x] Pastikan manual attendance approved ikut dihitung karena sudah masuk tabel `attendance`.
- [x] Pastikan attendance di luar `period_start` dan `period_end` tidak ikut.

Acceptance Criteria:

- [x] MID_MONTH period `2026-02` membaca attendance `2026-01-16` sampai `2026-02-15`.
- [x] MONTH_END period `2026-02` membaca attendance `2026-02-01` sampai `2026-02-28`.
- [x] Satu employee dengan assignment aktif lintas periode menghasilkan `working_days` yang stabil.

Target file:

- `app.py`
- Test terkait attendance/payroll.

### Phase 2: Payroll Calculation Sync

Status: Completed for payroll generator calculation path.

Bisa dikerjakan setelah helper Phase 1 tersedia.

Tasks:

- [x] Refactor payroll generator agar memakai `resolve_pay_cycle(...)`.
- [x] Refactor payroll generator agar memakai `calculate_attendance_summary_by_cycle(...)`.
- [x] Pastikan `PRORATED_ATTENDANCE` memakai:

```text
gross_salary = attendance_days x daily_rate
potongan_absen = 0
net_salary = gross_salary - potongan_telat - potongan_lain + tunjangan
```

- [x] Pastikan `FULL_MONTHLY_DEDUCTION` memakai:

```text
gross_salary = salary_base
potongan_absen = absent_days x daily_rate
net_salary = salary_base - potongan_absen - potongan_telat - potongan_lain + tunjangan
```

- [x] Pastikan tidak ada double penalty absen pada `PRORATED_ATTENDANCE`.
- [x] Simpan snapshot hasil resolver ke payroll record.
- [x] Approved payroll tidak boleh tergenerate ulang.

Acceptance Criteria:

- [x] Employee dengan hari hadir di scheme prorated tidak punya `potongan_absen`.
- [x] Employee dengan absen di scheme full monthly punya `potongan_absen`.
- [x] Total payroll sama antara detail dan list.

Target file:

- `app.py`
- `tests/`

### Phase 3: Data Contract & Integrity

Status: Partially completed.

Bisa dikerjakan paralel dengan Phase 2 jika perubahan schema backward-compatible.

Tasks:

- [x] Tambahkan field payroll jika belum ada:
  - `working_days`
  - `daily_rate`
  - `gross_salary`
  - `late_deduction_rate`
  - `absent_deduction_rate`
  - `calculation_version`
- [ ] Optional: tambahkan `policy_id` jika resolver sudah bisa mengembalikan policy source.
- [x] Pastikan migration tidak merusak payroll lama.
- [x] Untuk payroll lama, isi default aman:
  - `working_days = attendance_days + absent_days + leave_days` jika kosong.
  - `calculation_version = 'legacy'` jika kosong.
- [x] Payroll status `approved` harus immutable untuk:
  - regenerate
  - update adjustment
  - perubahan komponen hitung

Acceptance Criteria:

- [x] App start tanpa error di database lama.
- [ ] Payroll lama tetap bisa dibuka.
- [x] Payroll approved tidak berubah setelah policy diedit.

Target file:

- `app.py`
- SQLite migration helper existing.

### Phase 4: Dashboard Sync

Status: Partially completed.

Bisa dikerjakan paralel dengan Phase 1 untuk bagian tampilan field yang sudah tersedia.

Tasks Employee Dashboard:

- [x] Ubah attendance summary dari monthly menjadi pay-cycle based.
- [x] Tampilkan label periode aktif:
  - `period_start`
  - `period_end`
  - `payroll_schedule`
- [ ] Jangan ubah flow check-in / check-out kecuali perlu untuk data contract.

Tasks Client Admin Dashboard:

- [x] Payroll list default client-wide.
- [x] Tambahkan optional filter site.
- [x] Tampilkan:
  - `payroll_scheme`
  - `payroll_schedule`
  - `period_start`
  - `period_end`
  - `pay_date`
- [x] Generate payroll tetap dibatasi ke employee dalam client scope.

Tasks Admin / Superadmin Dashboard:

- [x] Pastikan filter tersedia:
  - client
  - site
  - payroll_schedule
  - period
  - status
- [x] Tampilkan `payroll_scheme` di list/detail.
- [ ] Pastikan admin bisa melihat multi-client, client admin tidak bocor ke client lain.

Acceptance Criteria:

- [x] Employee, Client Admin, dan Admin melihat period payroll yang sama.
- [x] Client Admin bisa melihat semua site dalam client.
- [x] Filter site mempersempit data, bukan menjadi default wajib.

Target file:

- `templates/dashboard/employee.html`
- `templates/dashboard/client.html`
- `templates/dashboard/admin_payroll.html`
- `static/js/dashboard_employee_mobile.js`
- `static/js/client_dashboard.js`

### Phase 5: Scope & Naming Cleanup

Status: Medium.

Kerjakan setelah Phase 2 stabil.

Tasks:

- [ ] Standardkan penggunaan `site_id` untuk site.
- [ ] Pertahankan `branch_id` hanya sebagai backward compatibility.
- [ ] Query baru harus prefer `site_id`.
- [ ] Response API payroll harus expose `site_id`, bukan hanya `branch_id`.
- [ ] Jangan hapus kolom lama sebelum ada migration plan.

Acceptance Criteria:

- [ ] Payroll list filter `site_id` konsisten.
- [ ] Attendance report filter `site_id` konsisten.
- [ ] Tidak ada data lama yang hilang.

Target file:

- `app.py`
- API response payroll/attendance terkait.

### Phase 6: Test Coverage & Regression Guard

Status: Partially completed.

Tasks:

- [x] Tambah test MONTH_END.
- [x] Tambah test MID_MONTH.
- [x] Tambah test `PRORATED_ATTENDANCE`.
- [x] Tambah test `FULL_MONTHLY_DEDUCTION`.
- [ ] Tambah test approved payroll immutable.
- [ ] Tambah test client admin tidak bisa akses payroll client lain.
- [x] Tambah test client admin bisa melihat semua site dalam client jika scope tenant-wide aktif.

Acceptance Criteria:

- [ ] Semua test existing tetap pass.
- [ ] Test baru membuktikan period alignment dan scheme calculation.
- [ ] Tidak ada regression attendance check-in / checkout.

Target file:

- `tests/`
- `test_api_attendance.py` jika pola existing masih dipakai.

## 8. Parallel Work Plan

Beberapa phase bisa dikerjakan sekaligus dengan aman:

| Jalur | Bisa Dikerjakan | Catatan |
| --- | --- | --- |
| A | Phase 1 | Fondasi backend, prioritas pertama. |
| B | Phase 3 | Aman jika migration backward-compatible. |
| C | Phase 4 read-only UI | Bisa mulai tampilkan field existing seperti period dan schedule. |
| D | Phase 6 test skeleton | Bisa siapkan scenario dulu, assertion detail mengikuti implementation. |

Urutan recommended:

1. Phase 1 + Phase 3 migration ringan.
2. Phase 2 payroll sync.
3. Phase 4 dashboard sync.
4. Phase 5 naming cleanup.
5. Phase 6 final regression.

## 9. Risk Control

Rules:

- Jangan ubah modul Patrol.
- Jangan ubah User Management.
- Jangan ganti framework.
- Jangan hapus kolom lama.
- Jangan ubah endpoint public tanpa backward compatibility.
- Jangan refactor besar di luar Attendance, Policy, dan Payroll.

Rollback safety:

- Semua schema change harus additive.
- Payroll approved tidak boleh diubah otomatis.
- Payroll draft boleh regenerate.
- Payroll lama harus tetap bisa dibuka walau field snapshot baru kosong.

## 10. Testing Checklist

### Period Alignment

- [ ] MONTH_END menghitung tanggal 1 sampai akhir bulan.
- [ ] MID_MONTH menghitung tanggal 16 bulan sebelumnya sampai 15 bulan berjalan.
- [ ] Attendance sebelum `period_start` tidak ikut.
- [ ] Attendance setelah `period_end` tidak ikut.

### Policy Resolution

- [ ] SITE override menang dari CLIENT.
- [ ] CLIENT menang dari GLOBAL.
- [ ] GLOBAL menang dari default.
- [ ] Resolver mengembalikan scheme dan schedule yang sama untuk payroll dan dashboard.

### Payroll Scheme

- [ ] PRORATED memakai `attendance_days`.
- [ ] PRORATED tidak menghitung `potongan_absen`.
- [ ] FULL_MONTHLY memakai `salary_base`.
- [ ] FULL_MONTHLY menghitung `potongan_absen`.
- [ ] Telat tidak terhitung ganda.

### Dashboard Consistency

- [ ] Employee summary sama periodenya dengan payroll.
- [ ] Client Admin melihat data client sendiri.
- [ ] Admin / Superadmin bisa filter client.
- [ ] Filter site konsisten.
- [ ] Filter schedule konsisten.

### Data Integrity

- [ ] Payroll menyimpan period snapshot.
- [ ] Payroll menyimpan policy snapshot.
- [ ] Approved payroll immutable.
- [ ] Payroll lama tetap terbaca.

## 11. Definition of Done

Selesai jika:

- Attendance payroll period sudah policy-based.
- Payroll calculation sudah scheme-based.
- Employee, Client Admin, dan Admin / Superadmin menampilkan data konsisten.
- Client Admin scope sudah tenant-wide dengan optional site filter.
- Test period, scheme, scope, dan immutability sudah ada.
- Tidak ada perubahan di luar scope Attendance / Policy / Payroll.
