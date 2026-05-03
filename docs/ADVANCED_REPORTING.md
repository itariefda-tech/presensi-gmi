# Advanced Reporting

Advanced Reporting adalah modul laporan analitik untuk mengubah data presensi, leave, lokasi, manual attendance, dan assignment menjadi insight operasional. Modul ini berada di menu **Reports** dan ditujukan untuk admin/HR/supervisor agar bisa memantau pola kehadiran, kedisiplinan, risiko fraud, dan performa client/site.

## Tujuan

- Memberi ringkasan kehadiran real-time berbasis data presensi.
- Membantu admin melihat pola telat, absen, leave, dan lokasi mencurigakan.
- Menyediakan dashboard performa client untuk kebutuhan monitoring dan pelaporan ke client.
- Menyediakan custom report builder agar report bisa disesuaikan tanpa membuat halaman baru.
- Mendukung export dan scheduling report untuk kebutuhan operasional rutin.

## Halaman dan Posisi UI

Advanced Reporting berada di `dashboard/admin_reports.html` dengan urutan card:

1. **HRIS Calendar Reports**
   Laporan schedule vs attendance, task completion, workload, coverage, dan late/absent by schedule.

2. **Reports Dashboard**
   Dashboard utama attendance dengan KPI, filter client/site/employee/tanggal, dan tabel attendance/late/absent.

3. **Advanced Reporting**
   Insight tambahan: ranking, leave pattern, geo anomaly, fraud detection, dan client performance.

4. **Custom Report Builder**
   Builder untuk memilih dimensi dan metric report, menjalankan custom report, dan menyimpan template.

Ada juga halaman fokus **Client Performance** di `dashboard/client_performance.html`.

## Filter

Filter utama Reports Dashboard dibuat mengkerucut:

- Pilih **Client** -> dropdown **Site** hanya menampilkan site milik client tersebut.
- Pilih **Site** -> dropdown **Employee** hanya menampilkan employee yang assignment aktifnya berada di site tersebut.
- Employee filter mengambil metadata assignment aktif dari backend.

Filter HRIS Calendar juga mengikuti pola yang sama.

## Modul yang Tersedia

### Attendance Analytics

Fungsi:
- Total hadir per periode.
- Total hadir harian.
- Total hadir per client.
- Total hadir per employee.
- Late count dan late rate.
- Rata-rata jam check-in.

Endpoint:
- `GET /api/report/attendance/summary`
- `GET /api/report/attendance/by-client`
- `GET /api/report/attendance/by-employee`
- `GET /api/report/attendance/ranking`

### Leave Analytics

Fungsi:
- Total leave per periode.
- Leave by type.
- Leave per employee.
- Frequent leave.
- Pola leave per hari.
- Average leave duration.

Endpoint:
- `GET /api/report/leave/pattern`

### Geo Analytics

Fungsi:
- Heatmap titik presensi.
- Deteksi lokasi di luar radius.
- Deteksi borderline radius.
- Daftar anomaly lokasi.

Endpoint:
- `GET /api/report/geo/heatmap`
- `GET /api/report/geo/anomaly`

### Fraud Detection

Fungsi:
- Deteksi check-in dan check-out kurang dari 5 menit.
- Deteksi lokasi presensi identik antar employee.
- Deteksi QR check-in berulang pada hari yang sama.
- Deteksi presensi di luar radius site.
- Risk score per employee.

Endpoint:
- `GET /api/report/anomaly`

### Client Performance

Fungsi:
- Attendance rate per client.
- Leave rate per client.
- Manual attendance count.
- Compliance score.
- Ranking client terbaik/terburuk.

Endpoint:
- `GET /api/report/client/performance`

UI:
- Panel di Advanced Reporting.
- Halaman fokus `Client Performance`.

### Export dan Scheduling

Fungsi:
- Export CSV.
- Export PDF sederhana.
- Export Excel-compatible (`.xls` berbasis CSV).
- Simpan schedule report mingguan/bulanan.

Endpoint:
- `GET /api/report/export`
- `POST /api/report/schedule`

Tabel:
- `report_schedules`

### Custom Report Builder

Fungsi:
- Pilih dimensi:
  - Date
  - Client
  - Site
  - Employee
- Pilih metric:
  - Present
  - Late Count
  - Leave Count
  - Absent Count
  - Manual Attendance
  - Attendance Rate
  - Late Rate
- Jalankan report custom.
- Simpan template report.
- Load template report tersimpan.

Endpoint:
- `POST /api/report/custom`
- `GET /api/report/templates`

Tabel:
- `report_templates`

## Data yang Dipakai

Advanced Reporting memakai data real dari tabel utama:

- `attendance`
- `leave_requests`
- `manual_attendance_requests`
- `assignments`
- `clients`
- `sites`
- `users`
- `employees`

Tidak ada dummy data untuk output report.

## Security dan Scope

- Advanced Reporting membutuhkan tier PRO/Enterprise dan add-on Advanced Reporting.
- Admin role dapat melihat report sesuai hak akses.
- Client role dibatasi pada client scope miliknya.
- Export dibatasi maksimal `REPORT_EXPORT_MAX_ROWS` baris.
- Endpoint list mendukung pagination dengan `limit`, `offset`, atau `page`.

## Optimasi

Optimasi yang sudah diterapkan:

- Index attendance untuk range report.
- Index attendance untuk email/date/action.
- Cache report ringan berbasis filter selama `REPORT_CACHE_TTL_SECONDS`.
- Pagination untuk output list agar UI dan response tidak terlalu berat.

## Parameter Umum Endpoint

Parameter umum yang digunakan:

- `start_date`: tanggal awal, format `YYYY-MM-DD`.
- `end_date`: tanggal akhir, format `YYYY-MM-DD`.
- `client_id`: filter client.
- `site_id`: filter site.
- `employee_id`: filter employee.
- `limit`: jumlah data per halaman.
- `offset`: offset data.
- `page`: halaman data.

## Catatan Product

Advanced Reporting difokuskan untuk operasional presensi employee, bukan untuk menganalisa admin/internal role. Karena itu UI utama memakai filter client, site, employee, dan tanggal. Filter role tetap dapat ditangani backend untuk kompatibilitas lama, tetapi tidak ditampilkan di UI utama.
