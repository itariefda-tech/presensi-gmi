# FEATURE ROADMAP: AI WORKFORCE INTELLIGENCE
## Module: AI Analysis Basic Rule-Based

## Objective
- [ ] Membuat fitur analisis otomatis berbasis data attendance
- [ ] Menghitung pegawai sering telat
- [ ] Menghitung pegawai sering absen
- [ ] Membuat ranking disiplin pegawai
- [ ] Memberikan insight dan rekomendasi HR
- [ ] Menjadi pondasi awal menuju predictive HR analytics enterprise

---

## Phase 0 — Feature Positioning
- [ ] Nama menu utama: AI Analysis
- [ ] Nama module enterprise: Workforce Intelligence
- [ ] Letakkan menu di dashboard Admin
- [ ] Tambahkan submenu:
  - [ ] Attendance Intelligence
  - [ ] Discipline Ranking
  - [ ] Employee Risk Insight
  - [ ] Department/Client Insight
  - [ ] Recommendation Center

---

## Phase 1 — Data Source Mapping
- [ ] Ambil data dari tabel attendance/presensi existing
- [ ] Ambil data employee
- [ ] Ambil data department/division jika tersedia
- [ ] Ambil data client jika tersedia
- [ ] Ambil data location jika tersedia
- [ ] Ambil data schedule/shift jika sudah ada
- [ ] Ambil data leave/izin/cuti jika tersedia
- [ ] Ambil data holiday jika tersedia
- [ ] Pastikan analysis tidak menghitung hari libur sebagai absen
- [ ] Pastikan izin/cuti resmi tidak dihitung sebagai absen buruk

---

## Phase 2 — Analysis Period Filter
- [ ] Tambahkan filter periode harian
- [ ] Tambahkan filter mingguan
- [ ] Tambahkan filter bulanan
- [ ] Tambahkan filter kuartal
- [ ] Tambahkan filter tahunan
- [ ] Tambahkan custom date range
- [ ] Tambahkan filter employee
- [ ] Tambahkan filter department
- [ ] Tambahkan filter client
- [ ] Tambahkan filter location
- [ ] Tambahkan filter shift
- [ ] Default periode: bulan berjalan

---

## Phase 3 — Core Metrics Attendance

### Late Metrics
- [ ] Hitung total keterlambatan per employee
- [ ] Hitung jumlah hari telat per employee
- [ ] Hitung rata-rata menit telat
- [ ] Hitung total menit telat
- [ ] Hitung telat paling parah dalam satu hari
- [ ] Hitung persentase telat dari total hari kerja
- [ ] Tandai employee sering telat jika telat > threshold

### Absence Metrics
- [ ] Hitung total absen tanpa keterangan
- [ ] Hitung total hari kerja seharusnya
- [ ] Hitung attendance rate
- [ ] Hitung absence rate
- [ ] Pisahkan absen tanpa keterangan
- [ ] Pisahkan izin
- [ ] Pisahkan cuti
- [ ] Pisahkan sakit
- [ ] Pisahkan libur/off day
- [ ] Tandai employee sering absen jika absence rate > threshold

### Discipline Metrics
- [ ] Hitung on-time rate
- [ ] Hitung attendance rate
- [ ] Hitung late penalty
- [ ] Hitung absence penalty
- [ ] Hitung early leave penalty jika data checkout tersedia
- [ ] Hitung missing checkout penalty jika data checkout tersedia
- [ ] Hitung final discipline score
- [ ] Buat ranking disiplin dari score tertinggi ke terendah

---

## Phase 4 — Rule-Based Scoring Engine

### Default Formula
- [ ] Base score setiap employee = 100
- [ ] Kurangi score untuk setiap telat
- [ ] Kurangi score berdasarkan total menit telat
- [ ] Kurangi score untuk absen tanpa keterangan
- [ ] Kurangi score untuk pulang cepat
- [ ] Kurangi score untuk missing checkout
- [ ] Jangan kurangi score untuk cuti/izin/sakit resmi
- [ ] Score minimum = 0
- [ ] Score maximum = 100

### Suggested Formula
- [ ] `discipline_score = 100`
- [ ] `discipline_score -= late_days * 2`
- [ ] `discipline_score -= total_late_minutes * 0.05`
- [ ] `discipline_score -= unexcused_absent_days * 8`
- [ ] `discipline_score -= early_leave_days * 3`
- [ ] `discipline_score -= missing_checkout_days * 2`
- [ ] Clamp score between 0 and 100

### Score Grade
- [ ] Grade A: 90–100 = Excellent
- [ ] Grade B: 80–89 = Good
- [ ] Grade C: 70–79 = Watchlist
- [ ] Grade D: 60–69 = Risk
- [ ] Grade E: 0–59 = Critical

---

## Phase 5 — Employee Classification

### Late Category
- [ ] Normal: telat 0–2 kali per bulan
- [ ] Attention: telat 3–5 kali per bulan
- [ ] Frequent Late: telat 6–9 kali per bulan
- [ ] Chronic Late: telat >= 10 kali per bulan

### Absence Category
- [ ] Normal: absen tanpa keterangan 0 kali
- [ ] Attention: absen 1 kali
- [ ] Risk: absen 2–3 kali
- [ ] Critical: absen >= 4 kali

### Discipline Category
- [ ] Excellent Discipline
- [ ] Stable Discipline
- [ ] Needs Attention
- [ ] High Risk
- [ ] Critical HR Action Required

---

## Phase 6 — AI Insight Text Generator

### Rule-Based Insight
- [ ] Generate insight otomatis per employee
- [ ] Generate insight otomatis per department
- [ ] Generate insight otomatis per client/location
- [ ] Generate summary bulanan
- [ ] Generate warning untuk HR

### Example Employee Insight
- [ ] Jika sering telat:
  - "Pegawai ini memiliki pola keterlambatan tinggi pada periode ini."
- [ ] Jika sering absen:
  - "Pegawai ini memiliki risiko kedisiplinan karena absen tanpa keterangan melebihi batas."
- [ ] Jika membaik:
  - "Disiplin pegawai menunjukkan perbaikan dibanding periode sebelumnya."
- [ ] Jika excellent:
  - "Pegawai memiliki konsistensi kehadiran sangat baik."

### Insight Tone
- [ ] Gunakan bahasa netral
- [ ] Jangan memakai bahasa menghukum
- [ ] Fokus pada data dan rekomendasi
- [ ] Hindari label personal yang bias

---

## Phase 7 — Recommendation Engine

### HR Recommendation
- [ ] Jika telat ringan: rekomendasikan reminder/supervisor coaching
- [ ] Jika telat kronis: rekomendasikan evaluasi shift/lokasi kerja
- [ ] Jika absen tinggi: rekomendasikan HR check-in
- [ ] Jika absen berulang: rekomendasikan surat peringatan sesuai policy
- [ ] Jika performa disiplin baik: rekomendasikan reward/recognition
- [ ] Jika pola telat terjadi di lokasi tertentu: rekomendasikan audit transport/lokasi/client
- [ ] Jika banyak pegawai telat di shift tertentu: rekomendasikan review jam shift

### Example Recommendation
- [ ] "Lakukan coaching oleh supervisor dalam 7 hari."
- [ ] "Review kecocokan jadwal shift dengan lokasi penempatan."
- [ ] "Periksa apakah keterlambatan terjadi karena faktor client/location."
- [ ] "Pertimbangkan recognition untuk pegawai dengan score konsisten > 95."

---

## Phase 8 — Dashboard AI Analysis

### Top Cards
- [ ] Total employee analyzed
- [ ] Average discipline score
- [ ] Total frequent late employee
- [ ] Total frequent absent employee
- [ ] Total high-risk employee
- [ ] Best discipline employee
- [ ] Worst discipline risk employee

### Charts
- [ ] Chart trend keterlambatan per minggu
- [ ] Chart trend absen per minggu
- [ ] Chart discipline score distribution
- [ ] Chart top 10 employee sering telat
- [ ] Chart top 10 employee sering absen
- [ ] Chart department/client dengan risiko tertinggi
- [ ] Chart attendance rate by location

### Tables
- [ ] Ranking disiplin employee
- [ ] Watchlist employee
- [ ] Chronic late employee
- [ ] High absence employee
- [ ] Improvement list
- [ ] Declining discipline list

---

## Phase 9 — Enterprise Drilldown

### Employee Drilldown
- [ ] Klik employee membuka detail analysis
- [ ] Tampilkan summary score
- [ ] Tampilkan attendance timeline
- [ ] Tampilkan hari telat
- [ ] Tampilkan menit telat
- [ ] Tampilkan hari absen
- [ ] Tampilkan pola jam masuk
- [ ] Tampilkan rekomendasi HR
- [ ] Tampilkan histori perubahan score

### Department Drilldown
- [ ] Tampilkan average score department
- [ ] Tampilkan employee risk count
- [ ] Tampilkan trend department
- [ ] Tampilkan top problem category

### Client/Location Drilldown
- [ ] Tampilkan attendance rate per client
- [ ] Tampilkan late rate per location
- [ ] Tampilkan shift paling bermasalah
- [ ] Tampilkan rekomendasi operasional

---

## Phase 10 — Comparison Analysis

### Period Comparison
- [ ] Bandingkan bulan ini vs bulan lalu
- [ ] Bandingkan minggu ini vs minggu lalu
- [ ] Hitung improvement score
- [ ] Hitung decline score
- [ ] Tandai employee membaik
- [ ] Tandai employee memburuk

### Example Output
- [ ] "Keterlambatan turun 12% dibanding bulan lalu."
- [ ] "Employee A membaik dari score 72 ke 86."
- [ ] "Location X mengalami kenaikan absence rate 8%."

---

## Phase 11 — Risk Alert System

### Alert Rules
- [ ] Alert jika employee telat >= 3 kali dalam 7 hari
- [ ] Alert jika employee absen tanpa keterangan >= 2 kali dalam 30 hari
- [ ] Alert jika discipline score turun > 15 poin dari bulan lalu
- [ ] Alert jika satu lokasi punya late rate > 25%
- [ ] Alert jika satu client punya absence rate > 10%
- [ ] Alert jika missing checkout tinggi
- [ ] Alert jika employee masuk kategori Critical

### Alert Level
- [ ] Info
- [ ] Warning
- [ ] High Risk
- [ ] Critical

### Alert Action
- [ ] Mark as reviewed
- [ ] Assign to HR
- [ ] Assign to Supervisor
- [ ] Add note
- [ ] Create coaching task
- [ ] Export evidence

---

## Phase 12 — AI Analysis Notes & Case Management

### HR Case Notes
- [ ] HR bisa menambahkan catatan pada employee risk
- [ ] Supervisor bisa menambahkan follow-up note
- [ ] Catatan memiliki timestamp
- [ ] Catatan memiliki author
- [ ] Catatan tidak bisa dilihat employee
- [ ] Catatan bisa dikaitkan dengan alert
- [ ] Catatan bisa dikaitkan dengan coaching task

### Case Status
- [ ] Open
- [ ] In Review
- [ ] Coaching Scheduled
- [ ] Resolved
- [ ] Escalated
- [ ] Closed

---

## Phase 13 — Privacy, Fairness, and Audit

### Privacy
- [ ] Hanya Admin/HR yang bisa melihat full AI Analysis
- [ ] Supervisor hanya melihat employee dalam scope-nya
- [ ] Employee hanya boleh melihat summary pribadinya jika diaktifkan
- [ ] Jangan tampilkan data sensitif tanpa permission
- [ ] Jangan jadikan AI Analysis sebagai keputusan otomatis final

### Fairness
- [ ] Jangan hitung cuti resmi sebagai absen buruk
- [ ] Jangan hitung sakit resmi sebagai pelanggaran
- [ ] Jangan hitung libur/off day sebagai absen
- [ ] Pisahkan masalah individu dan masalah lokasi/client
- [ ] Tampilkan disclaimer: analysis adalah alat bantu HR, bukan keputusan final

### Audit
- [ ] Simpan snapshot hasil analysis bulanan
- [ ] Simpan rule version yang dipakai
- [ ] Simpan siapa yang membuka detail analysis
- [ ] Simpan siapa yang mengubah threshold
- [ ] Simpan histori override/manual correction

---

## Phase 14 — Configuration Panel

### Threshold Setting
- [ ] HR/Admin bisa mengatur batas sering telat
- [ ] HR/Admin bisa mengatur batas sering absen
- [ ] HR/Admin bisa mengatur bobot penalty telat
- [ ] HR/Admin bisa mengatur bobot penalty absen
- [ ] HR/Admin bisa mengatur bobot missing checkout
- [ ] HR/Admin bisa mengatur grade score
- [ ] HR/Admin bisa mengatur alert rule

### Default Config
- [ ] Frequent late threshold = 5 kali/bulan
- [ ] Chronic late threshold = 10 kali/bulan
- [ ] Frequent absence threshold = 2 kali/bulan
- [ ] Critical absence threshold = 4 kali/bulan
- [ ] Late penalty per day = 2
- [ ] Absence penalty per day = 8
- [ ] Early leave penalty per day = 3
- [ ] Missing checkout penalty per day = 2

---

## Phase 15 — Reports & Export

### Reports
- [ ] Discipline Ranking Report
- [ ] Frequent Late Report
- [ ] Frequent Absence Report
- [ ] Attendance Risk Report
- [ ] Department Discipline Report
- [ ] Client/Location Discipline Report
- [ ] Monthly AI Analysis Summary
- [ ] Employee Individual Analysis Report

### Export
- [ ] Export Excel
- [ ] Export PDF
- [ ] Export filtered report
- [ ] Export employee evidence detail
- [ ] Export monthly snapshot

---

## Phase 16 — API / Backend Services

### Suggested Services
- [ ] `AIAnalysisService`
- [ ] `AttendanceMetricService`
- [ ] `DisciplineScoreService`
- [ ] `RiskAlertService`
- [ ] `InsightGeneratorService`
- [ ] `RecommendationService`
- [ ] `AnalysisSnapshotService`

### Suggested Endpoints
- [ ] `GET /admin/ai-analysis`
- [ ] `GET /admin/ai-analysis/summary`
- [ ] `GET /admin/ai-analysis/ranking`
- [ ] `GET /admin/ai-analysis/late-employees`
- [ ] `GET /admin/ai-analysis/absent-employees`
- [ ] `GET /admin/ai-analysis/employee/{id}`
- [ ] `GET /admin/ai-analysis/department/{id}`
- [ ] `GET /admin/ai-analysis/client/{id}`
- [ ] `GET /admin/ai-analysis/location/{id}`
- [ ] `POST /admin/ai-analysis/recalculate`
- [ ] `POST /admin/ai-analysis/alerts/{id}/review`
- [ ] `POST /admin/ai-analysis/cases`
- [ ] `GET /admin/ai-analysis/export`

---

## Phase 17 — Database Tables

### `ai_analysis_configs`
- [ ] id
- [ ] config_key
- [ ] config_value
- [ ] description
- [ ] updated_by
- [ ] created_at
- [ ] updated_at

### `ai_analysis_snapshots`
- [ ] id
- [ ] employee_id
- [ ] period_start
- [ ] period_end
- [ ] total_work_days
- [ ] present_days
- [ ] late_days
- [ ] absent_days
- [ ] total_late_minutes
- [ ] early_leave_days
- [ ] missing_checkout_days
- [ ] attendance_rate
- [ ] absence_rate
- [ ] discipline_score
- [ ] grade
- [ ] risk_level
- [ ] insight_text
- [ ] recommendation_text
- [ ] rule_version
- [ ] created_at
- [ ] updated_at

### `ai_analysis_alerts`
- [ ] id
- [ ] employee_id nullable
- [ ] department_id nullable
- [ ] client_id nullable
- [ ] location_id nullable
- [ ] alert_type
- [ ] alert_level
- [ ] title
- [ ] description
- [ ] metric_value
- [ ] threshold_value
- [ ] status
- [ ] assigned_to nullable
- [ ] reviewed_by nullable
- [ ] reviewed_at nullable
- [ ] created_at
- [ ] updated_at

### `ai_analysis_cases`
- [ ] id
- [ ] employee_id
- [ ] alert_id nullable
- [ ] case_title
- [ ] case_status
- [ ] priority
- [ ] assigned_to
- [ ] resolution_note nullable
- [ ] created_by
- [ ] created_at
- [ ] updated_at

### `ai_analysis_case_notes`
- [ ] id
- [ ] case_id
- [ ] note
- [ ] created_by
- [ ] created_at
- [ ] updated_at

---

## Phase 18 — UI Layout

### Main AI Analysis Page
- [ ] Header: AI Workforce Intelligence
- [ ] Filter periode
- [ ] Filter department/client/location
- [ ] Summary cards
- [ ] Trend charts
- [ ] Discipline ranking table
- [ ] Risk alerts table
- [ ] Recommendation center

### Employee Detail Page
- [ ] Employee profile summary
- [ ] Discipline score card
- [ ] Attendance metrics
- [ ] Timeline attendance
- [ ] AI insight
- [ ] HR recommendation
- [ ] Alert history
- [ ] Case notes
- [ ] Export button

---

## Phase 19 — Future Upgrade: Predictive AI

### Next-Level AI
- [ ] Predict employee absence risk minggu depan
- [ ] Predict employee lateness risk
- [ ] Detect abnormal attendance pattern
- [ ] Cluster employee by discipline behavior
- [ ] Forecast staffing shortage per client/location
- [ ] Recommend shift adjustment
- [ ] Recommend supervisor intervention timing

### Important
- [ ] Jangan implement machine learning dulu jika data belum cukup
- [ ] Mulai dari rule-based agar stabil dan transparan
- [ ] Siapkan struktur data agar nanti bisa upgrade ke ML
- [ ] Pastikan semua hasil AI bisa dijelaskan secara jelas
