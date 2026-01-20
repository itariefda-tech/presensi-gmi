# Audit UI/UX Speed & Delay (Performance)

Tanggal: 2026-01-21
Scope: Flask + Jinja templates + Tailwind + vanilla JS
Status: Draft / Ongoing

## Ringkasan Diagnosis

* [ ] Ada indikasi jank di sisi UI karena timer/animasi yang berjalan terus (clock 500ms + marquee/shimmer/blur), terutama di mobile dashboard.
* [ ] Beberapa halaman admin mengumpulkan data cukup banyak dalam satu request (overview, attendance, employees, assignments), berpotensi TTFB tinggi saat data tumbuh.
* [ ] Render tabel besar (attendance, approvals, manual attendance) bisa memperberat DOM dan repaint.
* [ ] Fetch pending approvals dipicu saat load halaman admin, bisa menambah delay render awal.
* [ ] Logging performa sebelumnya tidak ada; sekarang perlu ditambahkan untuk mengukur request + fungsi berat.

## Top Suspects (dengan Root Cause & Fix)

### 1) JS — timer & event handler (mobile)

* [ ] Lokasi: static/js/dashboard_employee_mobile.js (tickClock + resize handler)
* [ ] Gejala: UI mobile terasa berat/lag
* [ ] Bukti: setInterval(tickClock, 500) + window.addEventListener("resize", initNavPosition)
* [ ] Root cause: update UI terlalu sering + resize handler tanpa debounce
* [ ] Fix cepat:

  * [x] Ubah clock update menjadi 1s (bukan 500ms)
  * [x] Debounce resize 150ms
  * [x] Pause timer saat tab hidden (visibilitychange)
* [ ] Fix lanjutan:

  * [ ] requestIdleCallback untuk update non-kritis
  * [ ] Kurangi DOM writes pada setiap tick

### 2) CSS — animasi & efek berat

* [ ] Lokasi: static/css/app.css, static/css/dashboard.css, static/css/employee_mobile.css
* [ ] Gejala: repaint tinggi / scroll jank
* [ ] Bukti: animasi infinite (shimmer, marquee, blink) + blur/backdrop-filter
* [ ] Root cause: animasi konstan memaksa repaint
* [ ] Fix cepat:

  * [x] Implement prefers-reduced-motion untuk disable animasi/transisi
* [ ] Fix lanjutan:

  * [ ] Ganti shimmer/marquee dengan animasi sekali atau skeleton statis
  * [ ] Kurangi blur/backdrop-filter pada mobile

### 3) Backend — agregasi in-memory berat

* [ ] Lokasi: app.py -> _client_operational_summary
* [ ] Gejala: TTFB tinggi di /dashboard/admin saat data besar
* [ ] Bukti: memuat assignments + attendance + leave lalu loop agregasi
* [ ] Root cause: agregasi in-memory terhadap dataset besar
* [ ] Fix cepat:

  * [x] Tambahkan pengukuran durasi (PERF_LOG=1)
  * [ ] Batasi scope data (range tanggal / limit) bila aman
* [ ] Fix lanjutan:

  * [ ] Pindahkan agregasi ke SQL (GROUP BY)
  * [ ] Cache ringkasan harian

### 4) Backend/DB — list besar tanpa pagination

* [ ] Lokasi: app.py -> _attendance_live, _list_employees, _list_assignments
* [ ] Gejala: halaman admin attendance/employees lambat
* [ ] Bukti: query seluruh data + sorting/loop di Python
* [ ] Root cause: data besar tanpa pagination di server
* [ ] Fix cepat:

  * [x] Log ukuran hasil (count) + waktu query
  * [x] Terapkan limit default jika aman (misal 100–300 row)
* [ ] Fix lanjutan:

  * [x] Pagination server-side + filter tanggal/user/client
  * [ ] Lazy load (load more) di UI

### 5) Template/JS — fetch approvals saat load + render penuh

* [ ] Lokasi: templates/admin_approvals.html + static/js/dashboard_admin.js
* [ ] Gejala: loading awal “Memuat data…” lama
* [ ] Bukti: fetch /api/leave/pending saat load, lalu render semua rows
* [ ] Root cause: data pending besar + render tabel penuh
* [ ] Fix cepat:

  * [x] Spinner ringan + skeleton sederhana (tanpa shimmer berat)
  * [x] Limit/pagination dari server untuk pending
* [ ] Fix lanjutan:

  * [ ] Pagination + virtual list untuk tabel panjang

## Patch (Fix Cepat) — Target Implementasi

* [ ] app.py: tambah logging performa request + fungsi berat (aktif via env PERF_LOG=1)
* [ ] app.py: instrumentasi durasi di:

  * [x] _client_operational_summary
  * [x] _list_employees
  * [x] _list_assignments
  * [x] _list_leave_pending
  * [x] _fetch_manual_requests
  * [x] _attendance_live
* [ ] static/js/app.js: clock berhenti update saat tab hidden
* [ ] static/js/dashboard_employee_mobile.js:

  * [x] clock 1s + pause saat hidden
  * [x] debounce resize 150ms
* [ ] CSS (app.css/dashboard.css/employee_mobile.css):

  * [x] disable animasi/transisi saat prefers-reduced-motion

## Langkah Verifikasi (Sebelum/Sesudah)

### Backend

* [ ] Jalankan server dengan PERF_LOG=1
* [ ] Catat rute paling lambat: /dashboard/admin, /dashboard/admin/attendance, dll
* [ ] Bandingkan log REQ dan PERF sebelum/sesudah patch

### Frontend

* [ ] DevTools Performance: rekam saat buka dashboard (desktop & mobile emulation)
* [ ] Bandingkan: FPS, long tasks, paint time
* [ ] Uji prefers-reduced-motion aktif (setting OS/browser)

## Target Hasil

* [ ] TTFB turun pada halaman admin utama
* [ ] Long tasks berkurang, scroll lebih mulus di mobile
* [ ] Animasi tidak memaksa repaint saat user memilih reduce motion

## Catatan / Temuan Tambahan

* [ ] (Isi di sini jika menemukan root cause baru)
