# Advanced Reporting Roadmap

---

## PHASE 1 - DATA FOUNDATION (WAJIB, JANGAN LONCAT)
Tujuan: Pastikan data bisa dianalisa, bukan cuma disimpan

### Struktur Data
- [x] Tambahkan index pada tabel attendance (employee_email, created_at)
- [x] Tambahkan field:
  - [x] late_flag (bool)
  - [x] early_checkout_flag (bool)
  - [x] inside_radius_flag (bool)
- [x] Normalisasi format tanggal (YYYY-MM-DD)

### Helper Backend (app.py)
- [x] Buat helper:
  - [x] get_attendance_by_range(start, end)
  - [x] group_by_employee(data)
  - [x] group_by_client(data)
- [x] Buat util:
  - [x] calculate_late()
  - [x] calculate_work_duration()

### Endpoint Basic Analytics
- [x] GET /api/report/attendance/summary
- [x] GET /api/report/attendance/by-client
- [x] GET /api/report/attendance/by-employee

---

## PHASE 2 - BASIC ANALYTICS (FROM DATA TO INFORMASI)
Tujuan: Admin mulai melihat pola

### Attendance Analytics
- [x] Total hadir per hari
- [x] Total hadir per client
- [x] Total hadir per pegawai

### Leave Analytics
- [x] Total leave per periode
- [x] Leave by type (izin/sakit)
- [x] Leave per pegawai

### UI (Admin Dashboard)
- [x] Tambah menu: "Reports"
- [x] Tambah halaman:
  - [x] attendance_report.html
  - [x] leave_report.html

### Visual
- [x] Integrasi chart (Chart.js / ECharts)
- [x] Grafik:
  - [x] Line chart kehadiran
  - [x] Bar chart per client

---

## PHASE 3 - INTERMEDIATE ANALYTICS (INSIGHT MULAI MUNCUL)
Tujuan: Data mulai bicara

### Attendance Insight
- [x] Ranking pegawai paling disiplin
- [x] Ranking pegawai paling sering telat
- [x] Rata-rata jam check-in

### Leave Insight
- [x] Pegawai paling sering izin
- [x] Pola izin per hari (Senin/Jumat)
- [x] Durasi rata-rata leave

### Endpoint
- [x] GET /api/report/attendance/ranking
- [x] GET /api/report/leave/pattern

### UI
- [x] Card insight:
  - [x] "Top Performer"
  - [x] "Most Late"
  - [x] "Frequent Leave"

---

## PHASE 4 - GEO ANALYTICS (KILLER FEATURE)
Tujuan: Manfaatkan GPS (pembeda dari kompetitor)

### Data Processing
- [x] Hitung jarak dari titik valid
- [x] Tandai:
  - [x] near_radius_flag
  - [x] suspicious_location_flag

### Visual
- [x] Integrasi map (Leaflet / Google Maps)
- [x] Heatmap lokasi presensi

### Insight
- [x] Deteksi lokasi berulang
- [x] Deteksi presensi borderline radius

### Endpoint
- [x] GET /api/report/geo/heatmap
- [x] GET /api/report/geo/anomaly

---

## PHASE 5 - ANOMALY & FRAUD DETECTION (NAIK LEVEL)
Tujuan: Dari monitoring ke kontrol

### Rules Engine
- [x] Define rule:
  - [x] Check-in & check-out < 5 menit
  - [x] Lokasi identik antar pegawai
  - [x] QR digunakan berulang
- [x] Flag anomaly

### Output
- [x] List suspicious activity
- [x] Skor risiko per pegawai

### Endpoint
- [x] GET /api/report/anomaly

### UI
- [x] Halaman "Fraud Detection"
- [x] Badge merah untuk alert

---

## PHASE 6 - CLIENT PERFORMANCE DASHBOARD (JUALAN READY)
Tujuan: Bisa dijual ke client

### Metric
- [x] Attendance rate (%)
- [x] Leave rate
- [x] Manual attendance count
- [x] Compliance score

### Ranking
- [x] Ranking client terbaik / terburuk

### Endpoint
- [x] GET /api/report/client/performance

### UI
- [x] Halaman:
  - [x] client_performance.html
- [x] Scorecard per client

---

## PHASE 7 - EXPORT & SCHEDULING
Tujuan: Profesional & enterprise feel

### Export
- [x] Export PDF
- [x] Export Excel

### Scheduling
- [x] Generate report otomatis (mingguan/bulanan)
- [x] Kirim via email (opsional)

### Endpoint
- [x] GET /api/report/export
- [x] POST /api/report/schedule

---

## PHASE 8 - ADVANCED UX (PREMIUM FEEL)
Tujuan: Bukan cuma powerful, tapi enak dilihat

### UI/UX
- [x] Filter global:
  - [x] tanggal
  - [x] client
  - [x] role
- [x] Dashboard drag & drop widget
- [x] Dark/light sync

### Interaction
- [x] Drill-down:
  - [x] klik client -> detail pegawai
- [x] Tooltip insight otomatis

---

## PHASE 9 - CUSTOM REPORT BUILDER (SAAS LEVEL)
Tujuan: Fleksibel & scalable

### Feature
- [x] User pilih:
  - [x] metric
  - [x] dimensi
- [x] Simpan template report

### Endpoint
- [x] POST /api/report/custom
- [x] GET /api/report/templates

---

## PHASE 10 - FINAL HARDENING
Tujuan: Siap jual

### Quality
- [x] Validasi semua endpoint
- [x] Optimasi query (index, caching)
- [x] Pagination

### Security
- [x] Role-based access report
- [x] Limit export

### Final Check
- [x] Semua report real data (bukan dummy)
- [x] Tidak ada data mismatch
- [x] UI konsisten dengan theme system
