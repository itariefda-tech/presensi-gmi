# ROADMAP FEATURE: Tier add on; HRIS CALENDAR, TASK & SCHEDULING

## Objective
- [ ] Bangun fitur Calendar masuk ke dalam versi enterprise untuk aplikasi HRIS
- [ ] Menampilkan kalender besar di dashboard Admin
- [ ] Menyediakan task, jadwal kerja, event, notes, info, dan reminder
- [ ] Terintegrasi bertahap dengan employee dan attendance
- [x] Cocok untuk perusahaan outsource dengan banyak site/client

---

## Phase 0 — Repo Inspection
- [x] Cek framework frontend/backend yang digunakan
- [x] Identifikasi struktur routes
- [x] Identifikasi struktur controllers
- [x] Identifikasi struktur models
- [x] Identifikasi struktur migrations
- [x] Identifikasi struktur views/components
- [x] Identifikasi sidebar/menu dashboard Admin
- [x] Cari modul user/employee existing
- [x] Cari modul attendance/presensi existing
- [x] Cari modul dashboard admin existing
- [x] Cari modul role/permission existing
- [x] Jangan overwrite fitur existing
- [x] Ikuti naming convention repo

---

## Phase 1 — Basic Calendar Page
- [x] Tambahkan menu **Calendar** di dashboard utama Admin
- [x] Tentukan route: `/dashboard/admin/calendar`
- [x] Buat halaman Calendar
- [x] Tampilkan kalender besar mode month view
- [x] Tambahkan panel bawah kalender
- [x] Panel bawah berisi Today's Notes
- [x] Panel bawah berisi Today's Tasks
- [x] Panel bawah berisi Today's Schedule
- [x] Panel bawah berisi Important Info
- [x] Highlight tanggal hari ini
- [x] Tampilkan indicator event/task/schedule per tanggal
- [x] Pastikan halaman responsif desktop/tablet

---

## Phase 2 — Database Schema

### calendar_events
- [x] Buat tabel `calendar_events`
- [x] Tambahkan field `id`
- [x] Tambahkan field `title`
- [x] Tambahkan field `description` nullable
- [x] Tambahkan field `event_type`
- [x] Enum `event_type`: meeting, training, briefing, company_event, deadline, other
- [x] Tambahkan field `start_datetime`
- [x] Tambahkan field `end_datetime` nullable
- [x] Tambahkan field `site_label` nullable
- [x] Tambahkan field `client_id` nullable
- [x] Tambahkan field `created_by`
- [x] Tambahkan field `visibility`
- [x] Enum `visibility`: admin, supervisor, employee, all
- [x] Tambahkan field `color` nullable
- [x] Tambahkan field `status`
- [x] Enum `status`: scheduled, cancelled, done
- [x] Tambahkan timestamps

### calendar_tasks
- [x] Buat tabel `calendar_tasks`
- [x] Tambahkan field `id`
- [x] Tambahkan field `title`
- [x] Tambahkan field `description` nullable
- [x] Tambahkan field `assigned_to` nullable
- [x] Tambahkan field `assigned_by`
- [x] Tambahkan field `client_id` nullable
- [x] Tambahkan field `site_id` nullable
- [x] Tambahkan field `due_date`
- [x] Tambahkan field `start_datetime` nullable
- [x] Tambahkan field `end_datetime` nullable
- [x] Tambahkan field `priority`
- [x] Enum `priority`: low, medium, high, urgent
- [x] Tambahkan field `status`
- [x] Enum `status`: pending, in_progress, done, cancelled
- [x] Tambahkan timestamps

### employee_schedules
- [x] Buat tabel `employee_schedules`
- [x] Tambahkan field `id`
- [x] Tambahkan field `employee_id`
- [x] Tambahkan field `client_id` nullable
- [x] Tambahkan field `site_id` nullable
- [x] Tambahkan field `shift_name`
- [x] Tambahkan field `schedule_date`
- [x] Tambahkan field `start_time`
- [x] Tambahkan field `end_time`
- [x] Tambahkan field `break_start` nullable
- [x] Tambahkan field `break_end` nullable
- [x] Tambahkan field `status`
- [x] Enum `status`: scheduled, present, absent, late, swapped, cancelled
- [x] Tambahkan field `notes` nullable
- [x] Tambahkan field `created_by`
- [x] Tambahkan timestamps

### calendar_notes
- [x] Buat tabel `calendar_notes`
- [x] Tambahkan field `id`
- [x] Tambahkan field `note_date`
- [x] Tambahkan field `title`
- [x] Tambahkan field `content`
- [x] Tambahkan field `note_type`
- [x] Enum `note_type`: info, warning, reminder, supervisor_note, hr_note
- [x] Tambahkan field `visibility`
- [x] Enum `visibility`: admin, supervisor, employee, all
- [x] Tambahkan field `created_by`
- [x] Tambahkan timestamps

---

## Phase 3 — CRUD Calendar Data
- [x] Buat CRUD Event
- [x] Buat CRUD Task
- [x] Buat CRUD Schedule
- [x] Buat CRUD Note
- [ ] Klik tanggal membuka modal/detail drawer
- [x] Tambahkan tombol Add Event
- [x] Tambahkan tombol Add Task
- [x] Tambahkan tombol Add Schedule
- [x] Tambahkan tombol Add Note
- [x] Klik item calendar membuka detail
- [x] Tambahkan fitur edit item
- [x] Tambahkan fitur delete item
- [x] Validasi title wajib
- [x] Validasi date wajib
- [x] Validasi start time tidak boleh lebih besar dari end time, kecuali overnight shift
- [x] Validasi assigned employee harus valid
- [x] Validasi status harus sesuai enum

---

## Phase 4 — Calendar Event Display
- [x] Schedule/Shift berwarna blue
- [x] Task berwarna green
- [x] Meeting/Event berwarna purple
- [x] Deadline/Urgent berwarna red
- [x] Notes/Info berwarna yellow
- [x] Cancelled berwarna gray
- [x] Format item schedule: `08:00 Shift - Nama Employee`
- [x] Format item task: `Task: Nama Task`
- [x] Format item event: `Meeting: Nama Meeting`
- [x] Tambahkan filter All
- [x] Tambahkan filter Schedule
- [x] Tambahkan filter Task
- [x] Tambahkan filter Event
- [x] Tambahkan filter Notes
- [x] Tambahkan filter Client
- [x] Tambahkan filter Site
- [x] Tambahkan filter Employee
- [x] Tambahkan filter Status
- [x] Jika Site dipilih, filter Client otomatis none/hilang
- [x] Jika Site dipilih, filter Employee hanya menampilkan employee dengan assignment aktif di Site tersebut
- [x] Jika Client dipilih dan Site = All, filter Employee hanya menampilkan employee dengan assignment aktif di Client tersebut

---

## Phase 5 — HRIS Outsource Scheduling Logic
- [x] Support client assignment
- [x] Support site assignment
- [x] Admin bisa menjadwalkan employee ke client tertentu
- [x] Admin bisa menjadwalkan employee ke site tertentu
- [x] Admin bisa menjadwalkan employee ke shift tertentu
- [x] Deteksi employee punya dua jadwal overlap
- [x] Deteksi overnight shift
- [x] Jika `start_time > end_time`, anggap shift melewati tengah malam
- [x] Tampilkan conflict warning sebelum save
- [x] Admin boleh override conflict dengan confirmation
- [x] Helper functions implemented:
  - `_detect_schedule_overlap()`: detect overlapping schedules
  - `_times_overlap()`: handle overnight shift detection
  - Conflict warning system in schedule creation endpoint

---

## Phase 6 — Attendance Integration
- [x] Hubungkan schedule dengan presensi
- [x] Jika employee punya schedule hari itu, bandingkan attendance dengan jadwal
- [x] Tampilkan status On Time
- [x] Tampilkan status Late
- [x] Tampilkan status Absent
- [x] Tampilkan status Early Leave
- [x] Tampilkan status No Schedule
- [x] Pada detail schedule tampilkan jam masuk aktual
- [x] Pada detail schedule tampilkan jam keluar aktual
- [x] Pada detail schedule tampilkan keterlambatan
- [x] Helper function `_get_employee_attendance_status()` implemented
- [x] API endpoint `/api/admin/calendar/schedule/<id>/attendance` - get single schedule with attendance
- [x] API endpoint `/api/admin/calendar/schedules/monitoring` - get today's schedules with attendance status
- [x] Calendar bisa menjadi monitoring presensi harian
- [x] Admin bisa melihat siapa belum hadir dari jadwal hari ini

---

## Phase 7 — Role-Based Access
- [ ] Definisikan role Admin
- [ ] Definisikan role Supervisor
- [ ] Definisikan role Employee
- [ ] Admin bisa melihat semua calendar
- [ ] Admin bisa CRUD semua data
- [ ] Supervisor bisa melihat tim/client/site yang dia handle
- [ ] Supervisor bisa membuat task/schedule untuk timnya
- [ ] Supervisor tidak bisa edit data global admin kecuali diberi izin
- [ ] Employee hanya melihat jadwal sendiri
- [ ] Employee hanya melihat task sendiri
- [ ] Employee melihat event/info dengan visibility employee/all
- [ ] Employee bisa update status task sendiri jika diizinkan
- [ ] Pastikan data tidak bocor antar role

---

## Phase 8 — Dashboard Widgets
- [ ] Tambahkan widget Today Schedule
- [ ] Widget Today Schedule menampilkan jumlah employee scheduled
- [ ] Widget Today Schedule menampilkan jumlah present
- [ ] Widget Today Schedule menampilkan jumlah late
- [ ] Widget Today Schedule menampilkan jumlah absent
- [ ] Tambahkan widget Today Tasks
- [ ] Widget Today Tasks menampilkan pending
- [ ] Widget Today Tasks menampilkan in progress
- [ ] Widget Today Tasks menampilkan done
- [ ] Widget Today Tasks menampilkan urgent
- [ ] Tambahkan widget Upcoming Events
- [ ] Widget Upcoming Events menampilkan 5 event terdekat
- [ ] Tambahkan widget Alerts
- [ ] Alerts menampilkan shift conflict
- [ ] Alerts menampilkan absent without notice
- [ ] Alerts menampilkan urgent task overdue
- [ ] Tombol Calendar menjadi entry utama ke halaman detail

---

## Phase 9 — Notification & Reminder
- [ ] Reminder jadwal shift besok
- [ ] Reminder task deadline hari ini
- [ ] Reminder meeting/event
- [ ] Reminder task overdue
- [ ] Reminder perubahan jadwal
- [ ] Buat in-app notification
- [ ] Siapkan struktur future email notification
- [ ] Siapkan struktur future WhatsApp gateway
- [ ] Siapkan struktur future push notification
- [ ] User menerima reminder sesuai role
- [ ] Admin mendapat alert jika task/schedule bermasalah

---

## Phase 10 — Recurring Schedule
- [ ] Tambahkan repeat schedule daily
- [ ] Tambahkan repeat schedule weekly
- [ ] Tambahkan repeat schedule monthly
- [ ] Tambahkan pattern Senin–Jumat
- [ ] Tambahkan custom days
- [ ] Tambahkan shift rotation
- [ ] Tambahkan bulk schedule
- [ ] Bulk schedule bisa memilih banyak employee
- [ ] Bulk schedule bisa memilih client/site
- [ ] Bulk schedule bisa generate jadwal
- [ ] Cegah duplikat jadwal
- [ ] Conflict tetap dicek

---

## Phase 11 — Reports
- [ ] Buat Schedule vs Attendance Report
- [ ] Buat Task Completion Report
- [ ] Buat Employee Workload Report
- [ ] Buat Client Site Coverage Report
- [ ] Buat Late/Absent Report by Schedule
- [ ] Tambahkan filter tanggal
- [ ] Tambahkan filter client
- [ ] Tambahkan filter site
- [ ] Tambahkan filter employee
- [ ] Tambahkan export Excel
- [ ] Tambahkan export PDF optional
- [ ] Pastikan report bisa dipakai untuk audit dan billing client

---

## Suggested Implementation Order
- [x] Tambahkan route dan menu Calendar
- [x] Buat halaman UI kalender static
- [x] Buat migration tabel `calendar_events`
- [x] Buat migration tabel `calendar_tasks`
- [x] Buat migration tabel `employee_schedules`
- [x] Buat migration tabel `calendar_notes`
- [x] Buat model/entity
- [x] Buat API/controller CRUD
- [x] Integrasikan kalender dengan data backend
- [x] Tambahkan modal add/edit
- [x] Tambahkan filter
- [x] Tambahkan role access
- [ ] Integrasikan attendance
- [ ] Tambahkan dashboard widgets
- [ ] Tambahkan reminder
- [ ] Tambahkan recurring schedule
- [ ] Tambahkan report

---

## UI Layout
- [x] Header berisi title: Calendar
- [x] Header berisi button Add Event
- [x] Header berisi button Add Task
- [x] Header berisi button Add Schedule
- [x] Header berisi filter dropdown
- [x] Main area berisi large calendar month/week/day view
- [x] Bottom section berisi Selected Date Summary
- [x] Bottom section berisi Notes
- [x] Bottom section berisi Tasks
- [x] Bottom section berisi Schedules
- [x] Bottom section berisi Events
- [x] Right drawer/modal berisi detail selected item
- [x] Right drawer/modal memiliki action Edit
- [x] Right drawer/modal memiliki action Delete

---

## Definition of Done
- [x] Menu Calendar muncul di dashboard Admin
- [x] Calendar page bisa dibuka
- [x] Admin bisa CRUD event/task/schedule/note
- [x] Item tampil di kalender sesuai tanggal
- [x] Panel bawah menampilkan data tanggal terpilih
- [x] Data bisa difilter
- [x] Role access dasar berjalan
- [ ] Jadwal employee bisa dihubungkan dengan presensi
- [x] Tidak merusak fitur presensi existing
- [x] Code mengikuti struktur dan style repo
