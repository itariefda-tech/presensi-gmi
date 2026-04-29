# ROADMAP FEATURE: Tier add on; AI Analysis

## Objective
- [x] Menjadikan toggle add-on `AI` sebagai fitur **AI Analysis**
- [x] Menyediakan dashboard analisis operasional HRIS untuk Admin
- [x] Menganalisis attendance, schedule, task, workload, dan approval
- [x] Memberikan insight, risk signal, dan recommendation yang bisa diaudit
- [x] Menyimpan snapshot hasil analisis untuk riwayat

---

## Phase 0 — Repo Inspection
- [x] Identifikasi sistem add-on owner credential
- [x] Identifikasi permission dan sidebar dashboard Admin
- [x] Identifikasi sumber data attendance, schedule, task, leave, manual attendance
- [x] Ikuti pola Flask route, helper, template, dan SQLite migration repo

---

## Phase 1 — Add-on Gate & Navigation
- [x] Gunakan add-on existing `AI` / `ai` sebagai AI Analysis
- [x] Tambahkan permission `view_ai_analysis`
- [x] Tambahkan menu AI Analysis di sidebar Admin
- [x] Sembunyikan menu jika add-on AI belum aktif
- [x] Blokir halaman/API jika add-on AI belum aktif

---

## Phase 2 — Database Snapshot
- [x] Buat tabel `ai_analysis_snapshots`
- [x] Simpan range tanggal, client, site, summary, insights, risks, recommendations
- [x] Tambahkan index history/scope
- [x] Integrasikan migration ke init DB

---

## Phase 3 — Analysis Engine
- [x] Attendance health rate
- [x] Late pattern detection
- [x] Absent risk signal
- [x] Task completion analysis
- [x] Urgent/overdue task signal
- [x] Manual attendance pending signal
- [x] Employee workload signal
- [x] Recommendation generator

---

## Phase 4 — API
- [x] `GET /api/admin/ai-analysis/summary`
- [x] `POST /api/admin/ai-analysis/run`
- [x] `GET /api/admin/ai-analysis/history`
- [x] Filter tanggal, client, dan site
- [x] Snapshot generation

---

## Phase 5 — Admin UI
- [x] Halaman `/dashboard/admin/ai-analysis`
- [x] Filter tanggal, client, dan site
- [x] Preview analysis
- [x] Generate snapshot
- [x] Tampilkan summary KPI
- [x] Tampilkan insights
- [x] Tampilkan risks
- [x] Tampilkan recommendations
- [x] Tampilkan workload signals
- [x] Tampilkan snapshot history

---

## Backward Check - Source Phase 1 & Phase 4
- [x] Phase 1 data source mapping sesuai data repo yang tersedia: attendance, employee, client/site, schedule, task, leave/manual attendance
- [x] Phase 1 tidak menghitung leave resmi sebagai absen buruk melalui status `ON_LEAVE`
- [x] Phase 1 department/location/holiday belum dibuat sebagai tabel baru karena repo memakai client/site dan belum memiliki struktur holiday terpisah
- [x] Phase 4 scoring engine diterapkan per employee dengan base score 100, penalty late, late minutes, absent, early leave, dan missing checkout
- [x] Phase 4 score di-clamp 0-100 dan diberi grade A-E

---

## Source Phase 5 - Employee Classification
- [x] Kategori late: Normal, Attention, Frequent Late, Chronic Late
- [x] Kategori absence: Normal, Attention, Risk, Critical
- [x] Kategori discipline: Excellent Discipline, Stable Discipline, Needs Attention, High Risk, Critical HR Action Required
- [x] Tambahkan `employee_analysis` ke payload API summary/run
- [x] Tampilkan klasifikasi employee di Admin UI

---

## Source Phase 6 - Rule-Based Insight Text Generator
- [x] Generate insight otomatis per employee
- [x] Insight memakai bahasa netral dan berbasis data attendance
- [x] Insight membedakan frequent late, absence risk, excellent discipline, dan kondisi stabil/perlu perhatian
- [x] Summary insight menampilkan discipline score, frequent late employee, dan high-risk employee
- [x] Risk list menampilkan employee discipline risk prioritas

---

## Source Phase 7 - Recommendation Engine
- [x] Rekomendasi reminder/coaching untuk telat ringan
- [x] Rekomendasi review shift/lokasi untuk frequent/chronic late
- [x] Rekomendasi HR check-in untuk absen berulang
- [x] Rekomendasi policy follow-up untuk absence critical
- [x] Rekomendasi recognition untuk score tinggi
- [x] Rekomendasi global untuk frequent late, frequent absent, dan high-risk employee

---

## Source Phase 8 - Dashboard AI Analysis
- [x] Top cards: total employee analyzed, average discipline score, frequent late, frequent absent, high-risk employee
- [x] Top cards: best discipline employee dan worst discipline risk employee tersedia di payload summary
- [x] Chart ringan berbasis HTML/CSS untuk weekly late trend
- [x] Chart ringan berbasis HTML/CSS untuk weekly absent trend
- [x] Chart ringan berbasis HTML/CSS untuk discipline score distribution
- [x] Chart ringan berbasis HTML/CSS untuk site risk dan attendance rate by location payload
- [x] Tabel ranking discipline employee
- [x] Tabel watchlist employee
- [x] Tabel chronic late employee
- [x] Tabel high absence employee
- [x] Improvement list dan declining list tersedia melalui period comparison

---

## Source Phase 9 - Enterprise Drilldown
- [x] Klik employee membuka modal detail analysis
- [x] Detail employee menampilkan summary score, grade, late days, late minutes, absent days, attendance rate
- [x] Detail employee menampilkan attendance timeline
- [x] Detail employee menampilkan pola jam masuk
- [x] Detail employee menampilkan insight dan rekomendasi HR
- [x] Client/location drilldown tersedia lewat table Site Insight: attendance rate, late rate, absence rate, problem shift, recommendation
- [x] Department drilldown belum dibuat sebagai tabel baru karena repo belum memiliki struktur department terpisah

---

## Source Phase 10 - Comparison Analysis
- [x] Bandingkan periode aktif dengan periode sebelumnya dengan panjang range yang sama
- [x] Hitung attendance rate delta
- [x] Hitung late rate delta
- [x] Hitung average discipline score delta
- [x] Tandai employee membaik jika score naik minimal 5 poin
- [x] Tandai employee memburuk jika score turun minimal 5 poin
- [x] Tampilkan improvement list dan declining discipline list

---

## Source Phase 11 - Risk Alert System
- [x] Alert employee telat >= 3 kali pada periode aktif
- [x] Alert employee absen tanpa keterangan >= 2 kali pada periode aktif
- [x] Alert average discipline score turun > 15 poin dibanding periode sebelumnya
- [x] Alert lokasi late rate > 25%
- [x] Alert lokasi absence rate > 10%
- [x] Alert employee kategori Critical HR Action Required
- [x] Alert level: info, warning, high_risk, critical
- [x] Alert action metadata: mark reviewed, assign HR/supervisor, add note, create coaching task, export evidence

---

## Source Phase 12 - AI Analysis Notes & Case Management
- [x] Buat tabel `ai_analysis_cases`
- [x] Buat tabel `ai_analysis_case_notes`
- [x] HR/Admin/Supervisor bisa membuat follow-up case dari drilldown employee
- [x] Case note memiliki timestamp dan author
- [x] Case note hanya tersedia di dashboard Admin AI Analysis, tidak ditampilkan ke employee
- [x] Case bisa dikaitkan dengan alert type / employee risk
- [x] Status case: open, in_review, coaching_scheduled, resolved, escalated, closed
- [x] API cases: list, create, add note, update status

---

## Source Phase 13 - Privacy, Fairness, and Audit
- [x] Full AI Analysis tetap di-gate oleh add-on AI dan permission Admin dashboard
- [x] Supervisor scope dipersempit ke `site_id` atau `client_id` miliknya jika tersedia
- [x] Employee tidak memiliki menu/API full AI Analysis
- [x] Fairness notice tampil di UI: AI Analysis alat bantu HR, bukan keputusan otomatis final
- [x] Cuti/izin resmi tetap tidak dihitung sebagai absen buruk melalui `ON_LEAVE`
- [x] Masalah individu dan lokasi/client dipisah dalam employee analysis dan site insight
- [x] Snapshot menyimpan rule version
- [x] Audit log untuk view employee detail, config update, export, snapshot, case, dan case note

---

## Source Phase 14 - Configuration Panel
- [x] Buat tabel `ai_analysis_configs`
- [x] HR/Admin bisa mengatur batas frequent/chronic late
- [x] HR/Admin bisa mengatur batas frequent/critical absence
- [x] HR/Admin bisa mengatur penalty late, late minutes, absence, early leave, missing checkout
- [x] HR/Admin bisa mengatur minimum grade score A/B/C/D
- [x] HR/Admin bisa mengatur alert rule: late threshold, absence threshold, score drop, site late/absence rate
- [x] Default config tersedia sesuai roadmap
- [x] Config mempengaruhi scoring, kategori, dan alert engine

---

## Source Phase 15 - Reports & Export
- [x] Discipline Ranking Report
- [x] Frequent Late Report
- [x] Frequent Absence Report
- [x] Attendance Risk Report
- [x] Client/Location Discipline Report
- [x] Monthly AI Analysis Summary
- [x] Employee Individual Analysis Report
- [x] Export Excel CSV
- [x] Export PDF sederhana
- [x] Export filtered report memakai filter tanggal/client/site aktif
- [x] Export monthly snapshot/evidence tercatat di audit log

---

## Source Phase 16 - API / Backend Services
- [x] Tambahkan service facade monolith: `AIAnalysisService`, `AttendanceMetricService`, `DisciplineScoreService`, `RiskAlertService`, `InsightGeneratorService`, `RecommendationService`, `AnalysisSnapshotService`
- [x] Endpoint summary tersedia di `/api/admin/ai-analysis/summary` dan alias `/admin/ai-analysis/summary`
- [x] Endpoint ranking tersedia di `/api/admin/ai-analysis/ranking` dan alias `/admin/ai-analysis/ranking`
- [x] Endpoint frequent late tersedia di `/api/admin/ai-analysis/late-employees` dan alias `/admin/ai-analysis/late-employees`
- [x] Endpoint frequent absent tersedia di `/api/admin/ai-analysis/absent-employees` dan alias `/admin/ai-analysis/absent-employees`
- [x] Endpoint employee drilldown tersedia di `/api/admin/ai-analysis/employee/{id}` dan alias `/admin/ai-analysis/employee/{id}`
- [x] Endpoint client insight tersedia di `/api/admin/ai-analysis/client/{id}` dan alias `/admin/ai-analysis/client/{id}`
- [x] Endpoint location insight tersedia di `/api/admin/ai-analysis/location/{id}` dan alias `/admin/ai-analysis/location/{id}`
- [x] Endpoint department placeholder tersedia dan aman sampai tabel department dibuat
- [x] Endpoint recalculate tersedia di `/api/admin/ai-analysis/recalculate` dan alias `/admin/ai-analysis/recalculate`
- [x] Endpoint alert review tersedia di `/api/admin/ai-analysis/alerts/{id}/review` dan alias `/admin/ai-analysis/alerts/{id}/review`
- [x] Endpoint case management dan export tersedia dengan alias `/admin/ai-analysis/*`

## Source Phase 17 - Database Tables
- [x] `ai_analysis_configs` tersedia untuk threshold, penalty, grade, dan alert rule
- [x] `ai_analysis_snapshots` diperluas dengan kolom metric roadmap: employee, work days, present, late, absent, late minutes, early leave, missing checkout, rate, score, grade, risk, insight, recommendation
- [x] Snapshot aggregate tetap backward-compatible melalui JSON summary/insight/risk/recommendation
- [x] Snapshot sekarang menyimpan `alerts_json`, `rule_version`, dan `updated_at`
- [x] `ai_analysis_alerts` tersedia dan snapshot run menyimpan alert generated ke tabel
- [x] `ai_analysis_cases` tersedia untuk follow-up HR/Supervisor
- [x] `ai_analysis_case_notes` tersedia untuk timestamped notes
- [x] Index scope, employee, alert status, case status, dan case notes tersedia

## Source Phase 18 - UI Layout
- [x] Main page memiliki header AI Analysis/Workforce Intelligence context
- [x] Filter periode, client, dan location/site tersedia
- [x] Summary cards, charts ringan, ranking, alert, recommendation center, case management, dan history tersedia
- [x] Employee detail modal menampilkan score, attendance metrics, timeline, insight, recommendation, dan case note
- [x] UI menampilkan fairness notice bahwa AI Analysis bukan keputusan otomatis final
- [x] Layout menambahkan panel Predictive AI Readiness untuk phase 19

## Source Phase 19 - Future Upgrade: Predictive AI
- [x] Machine learning tidak diimplementasikan dulu sesuai constraint roadmap
- [x] Payload `predictive_readiness` disiapkan sebagai pondasi upgrade ML transparan
- [x] Readiness menghitung data points, minimum recommended points, status, dan notes
- [x] Rule-based risk preview disediakan untuk calon absence/lateness risk tanpa mengklaim prediksi ML
- [x] Site forecast foundation disediakan dari risk score lokasi untuk future staffing/shift recommendation
