Audit statis selesai. `python -m py_compile app.py` OK. Saya tidak mengubah file; worktree sudah punya perubahan existing di `templates/dashboard/admin_clients.html`.

🔴 CRITICAL (HARUS DIPERBAIKI)

1. Secret dan admin seed masih insecure (BLOCKER)  
Dampak: session bisa dipalsukan jika `FLASK_SECRET` kosong, dan deployment bisa punya akun admin publik `hrd@gmi.com/hrd123`.  
Lokasi: [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:59>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:2969>), [README.md](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/README.md:16>)  
Solusi: fail-fast jika secret kosong, default `ENABLE_SEED_DATA=0`, hapus credential default dari production path.

2. Endpoint upload dan owner add-on terbuka publik (BLOCKER)  
Dampak: siapa pun bisa upload file gambar ke static, dan owner add-on bisa dibuka dengan default `owner123`; ini bisa mengubah entitlement global.  
Lokasi: [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:506>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:524>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:3043>)  
Solusi: wajibkan login `hr_superadmin`, CSRF, rate limit, password dari env wajib, dan pindahkan upload ke storage terkontrol.

3. Feature lock Phase 2 bisa dibypass via API (BLOCKER)  
Dampak: user Basic masih bisa submit manual attendance via `/api/attendance/manual`, employee masih bisa scan QR jika payload valid, dan `/dashboard/admin/qr/payload` tidak cek tier.  
Lokasi: [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:1974>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:1682>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:10497>)  
Solusi: buat guard entitlement backend terpusat untuk QR/manual/payroll/reporting; UI lock hanya pendukung, bukan kontrol utama.

4. Flow master employee → signup → attendance putus (BLOCKER)  
Dampak: client membuat employee sebelum user ada, assignment tidak dibuat; setelah signup `SUDAHBYADMIN`, user aktif tetapi gagal check-in karena tidak punya active assignment.  
Lokasi: [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:729>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:342>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:1724>)  
Solusi: simpan pending assignment berbasis email, lalu attach saat signup, atau ubah assignment memakai `employee_id` sebagai sumber utama.

5. Data attendance tidak konsisten: `checkin/checkout` vs `IN/OUT` (BLOCKER)  
Dampak: manual approval bisa membuat duplikasi hari yang sama, dashboard menghitung hanya `checkin`, payroll/reporting menghitung campuran `IN/checkin`.  
Lokasi: [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:7322>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:8583>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:3577>)  
Solusi: normalisasi enum action ke satu format, migrasi data lama, dan buat unique index memakai action normalisasi.

🟠 HIGH PRIORITY

1. Roadmap Phase 1 checklist tidak sesuai endpoint aktual (RISKY)  
Dampak: roadmap menulis `POST /api/leave/create`, implementasi hanya `/api/leave/request`; integrasi eksternal akan gagal. Backend juga tidak validasi format tanggal atau `date_to >= date_from`.  
Lokasi: [roadmap_upgrade_hris.md](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/roadmap_upgrade_hris.md:23>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:2777>)  
Solusi: tambah alias `/api/leave/create`, validasi tanggal backend, cegah range terbalik/overlap bila dibutuhkan.

2. Payroll Phase 2 belum production-ready (RISKY)  
Dampak: semua user default `basic` dan tidak ada UI/API set tier; payroll malah dikunci add-on `payroll_plus`, approval payroll hanya placeholder.  
Lokasi: [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:6602>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:11555>), [admin_payroll.html](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/templates/dashboard/admin_payroll.html:595>)  
Solusi: buat admin tier management, pisahkan payroll basic vs payroll_plus, dan implement approve/detail/update payroll atau hapus tombolnya.

3. Reporting Basic tidak benar-benar terpasang (RISKY)  
Dampak: ada `admin_reports.html`, tetapi tidak ada route/menu; template memanggil `/api/clients` yang tidak ada. API report juga dikunci add-on advanced, bukan basic.  
Lokasi: [admin_reports.html](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/templates/dashboard/admin_reports.html:410>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:2210>)  
Solusi: buat route/menu reports, endpoint `/api/clients`, dan bedakan report basic vs advanced.

4. Payroll/reporting memakai asumsi hardcoded (RISKY)  
Dampak: telat selalu dibandingkan `08:00`, payroll selalu 22 hari kerja, tidak mengikuti shift/policy/client. Hasil gaji dan KPI bisa salah.  
Lokasi: [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:8032>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:8072>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:8245>)  
Solusi: hitung dari assignment shift + attendance policy, bukan konstanta global.

5. Password reset belum punya delivery flow (RISKY)  
Dampak: `/api/auth/forgot` membuat token, tapi tidak mengirim email/WhatsApp kecuali `SHOW_RESET_TOKEN` untuk debug; user production tidak bisa menyelesaikan reset.  
Lokasi: [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:352>)  
Solusi: integrasi provider email/WA atau nonaktifkan UI forgot sampai delivery siap.

🟡 MEDIUM

1. Role roadmap tidak sinkron: `koordinator` tidak ada  
Dampak: roadmap menyebut “Koordinator fallback”, kode memakai `manager_operational`; acceptance criteria approval jadi ambigu.  
Lokasi: [roadmap_upgrade_hris.md](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/roadmap_upgrade_hris.md:32>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:2979>)  
Solusi: pilih satu istilah role, migrasi role lama, update roadmap/README/UI.

2. Method attendance tidak stabil: `gps_selfie` vs `gps+selfie`  
Dampak: frontend badge dan filter bisa salah membaca method.  
Lokasi: [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:1828>), [dashboard_employee_mobile.js](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/static/js/dashboard_employee_mobile.js:493>)  
Solusi: simpan satu enum canonical, misalnya `gps_selfie`.

3. GPS/security attendance masih mudah dimanipulasi  
Dampak: backend menerima `device_time` dan `lat/lng` dari client; `accuracy` diparse tapi tidak dipakai.  
Lokasi: [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:1760>), [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:3422>)  
Solusi: pakai server time sebagai waktu utama, validasi accuracy, simpan raw device metadata untuk audit.

4. API approval tidak konsisten  
Dampak: `/api/leave/approve` juga dipakai untuk reject, sementara roadmap punya approval center unified `/api/approval/pending` yang tidak dipakai UI.  
Lokasi: [app.py](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/app.py:2094>), [admin_approvals.html](<C:/Users/Administrator/OneDrive/Documents/GitHub/Presensi/templates/dashboard/admin_approvals.html:129>)  
Solusi: pisahkan `/approve` dan `/reject`, atau dokumentasikan action-based endpoint konsisten.

🟢 LOW / IMPROVEMENT

1. Orphan/dead feature cukup banyak  
Dampak: noise maintenance dan potensi bug dari kode lama. Contoh: `admin_reports.html` tanpa route, `admin_shifts.html` refer endpoint shift yang tidak ada, `dashboard_employee.js` tidak diload, helper `_is_enterprise`, `_approve_manual_request`, `_insert_manual_attendance_record` tidak dipanggil.  
Solusi: hapus, sambungkan, atau tandai deprecated.

2. Repo hygiene lemah  
Dampak: repo membengkak dan rawan salah deploy. Ada `git-setup.exe`, `python-3.13.10-amd64.exe`, `.bak`, script/debug file.  
Solusi: keluarkan binary/debug dari git, pindahkan tooling ke release/docs.

🔥 TOP 5 MASALAH PALING BERBAHAYA

1. Default secret + seed admin publik.  
2. Public upload dan owner add-on endpoint.  
3. Feature lock PRO bisa dibypass via API.  
4. Assignment tidak otomatis tersambung setelah signup master employee.  
5. Attendance action campur `checkin` dan `IN`, menyebabkan duplikasi dan laporan salah.

🧱 REKOMENDASI ARSITEKTUR

Current structure belum scalable: `app.py` sudah terlalu besar dan mencampur route, DB schema, business logic, reporting, payroll, dan patrol. Refactor paling masuk akal: pisah blueprint `auth`, `attendance`, `leave`, `approval`, `payroll`, `admin`, `client`, lalu pindahkan logic ke service layer. Tambahkan migration layer eksplisit untuk schema dan enum (`attendance_action`, `attendance_method`, `leave_status`). Entitlement tier/add-on harus jadi satu service backend, bukan tersebar di route/template.

🚀 NEXT STEP PALING MASUK AKAL

1. Freeze Phase 4 dulu; jangan tambah fitur sebelum blocker Phase 1-3 selesai.  
2. Patch security: secret wajib, seed off, public upload/owner add-on wajib auth.  
3. Normalisasi attendance action/method dan migrasi data.  
4. Perbaiki flow employee assignment setelah signup.  
5. Buat test Flask `test_client` untuk login, check-in, manual approval, leave approval, tier lock, dan payroll/report access.