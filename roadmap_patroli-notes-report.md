📌 Roadmap Feature: Patrol, Catatan & Reporting System

Project: presensi-gmi
Tier: Add-on (Pro) + Included (Enterprise)
Status: In Development

🎯 1. OBJECTIVE

Mengembangkan sistem presensi menjadi:

❌ Bukan hanya absensi
✅ Platform kontrol operasional lapangan (security, logistik, site monitoring)

Fitur ini memungkinkan:

Pegawai mencatat aktivitas real-time
Admin memonitor dan mengambil keputusan
Client mendapatkan transparansi operasional
🧠 2. CORE CONCEPT
👮 Pegawai

“Sensor lapangan / input realita”

🧑‍💼 Admin

“Control room / decision maker”

🔁 3. END-TO-END FLOW
Login → Check-in → Aktivitas → Sync → Monitoring Admin → Validasi → Check-out
Detail:
Pegawai login
Check-in
Input aktivitas selama shift
Data dikirim ke server
Admin melihat secara real-time
Supervisor merespon / validasi
Pegawai check-out
👮 4. EMPLOYEE DASHBOARD (MOBILE-FIRST)
🎯 Prinsip UX
Cepat
Minim klik
Tidak membingungkan
📱 4.1 HOME SCREEN
🔷 Section: OPERASIONAL HARI INI

Menampilkan:

Status: ON DUTY / OFF DUTY
Last activity
Quick action buttons
[ + Catatan ]
[ Gate Log ]
[ Insiden ]
[ Patrol Scan ]
[ Handover ]
⚡ 4.2 QUICK ACTION MODULES
➕ 1. Activity Log

Flow:

Klik “+ Catatan”
Pilih jenis aktivitas
Isi catatan (opsional)
Tambah foto (opsional)
Submit

Auto Capture:

Timestamp
GPS
🚗 2. Gate Log

Flow:

Klik “Gate Log”
Pilih masuk / keluar
Input:
Plat nomor
Jenis kendaraan
Foto kendaraan
Submit
🚨 3. Incident Report

Flow:

Klik “Insiden”
Pilih kategori
Pilih severity
Deskripsi
Foto
Submit

🔥 Enhancement:

Tombol EMERGENCY (panic button)
Trigger notifikasi admin langsung
📍 4. Patrol System

Flow:

Klik “Patrol Scan”
Scan QR checkpoint
Auto log:
Waktu
Lokasi
Submit otomatis
🔄 5. Handover

Flow:

Klik “Handover”
Checklist:
Pintu
CCTV
Listrik
Catatan tambahan
Foto kondisi
Submit
📊 4.3 ACTIVITY TIMELINE

Menampilkan semua aktivitas harian:

Activity log
Gate log
Incident
Patrol

Tujuan:

Memberi feedback visual bahwa pekerjaan tercatat

🧑‍💼 5. ADMIN DASHBOARD (CONTROL ROOM)
🎯 Prinsip
Real-time visibility
Tidak perlu turun lapangan
Semua data terpusat
🧭 5.1 MENU STRUCTURE
Patrol System
├── Live Activity
├── Gate Log
├── Incident
├── Patrol Tracking
├── Handover
└── Reports
📡 5.2 LIVE ACTIVITY (CORE FEATURE)

Tampilan:

Feed realtime seperti timeline

Menampilkan:

Nama pegawai
Aktivitas
Waktu
Lokasi
Foto (thumbnail)

Teknis:

Polling (awal)
WebSocket (upgrade)
🚗 5.3 GATE MONITORING

Tabel:

Waktu
Gate
Plat nomor
Foto
Petugas
🚨 5.4 INCIDENT DASHBOARD

Visual:

Highlight berdasarkan severity
Level	Warna
Critical	🔴 Merah
Warning	🟡 Kuning

Fitur:

Detail view
Supervisor note
Status update
📍 5.5 PATROL TRACKING

Menampilkan:

Checkpoint yang sudah discan
Checkpoint yang terlewat

Future:

Map tracking (GPS trail)
🔄 5.6 HANDOVER MONITOR

Menampilkan:

Shift transition
Petugas sebelumnya
Petugas berikutnya
Catatan
📊 5.7 REPORT SYSTEM

Filter:

Client
Site
Tanggal

Output:

Ringkasan aktivitas
Total insiden
Performa pegawai
🔗 6. DATA SYNCHRONIZATION RULE
🔥 Mandatory Rules
1. Real-time visibility

Semua input pegawai langsung muncul di admin

2. Supervisor interaction

Tambahkan field:

supervisor_note
status
3. Notification system (Phase 2)
Incident critical → notif admin
Patrol miss → alert
🧱 7. TECHNICAL FLOW
Pegawai:
UI → POST API → Database
Admin:
GET API → Render Dashboard
Sync:
Polling 5–10 detik
Upgrade → WebSocket
⚠️ 8. COMMON PITFALLS
❌ Terlalu banyak menu

→ user bingung

❌ Input terlalu panjang

→ user malas

❌ Admin tidak informatif

→ client tidak melihat value

🧭 9. IMPLEMENTATION PRIORITY
🥇 Phase 1 (Core MVP)
Activity Log
Gate Log
Live Activity Dashboard
🥈 Phase 2
Incident System
Handover
🥉 Phase 3
Patrol Tracking
Reporting & Analytics
💡 10. IDE TAMBAHAN (VALUE UPGRADE)

Berikut ide segar untuk meningkatkan value produk:

🔔 A. Smart Notification System
WhatsApp / Telegram alert
Email report otomatis
📊 B. Client Portal
Client bisa login
Lihat laporan site mereka sendiri
📈 C. Performance Scoring
Skor pegawai otomatis
KPI based system
🧠 D. AI Insight (Future)
Deteksi:
pegawai malas patroli
area rawan incident
📷 E. Photo Verification
AI detect:
foto valid / fake
lokasi sesuai / tidak
🗺️ F. Geo-Fencing
Check-in hanya di area tertentu
Patrol wajib di titik tertentu
🔐 G. Enterprise Differentiator

Untuk paket enterprise:

Multi-site management
SLA reporting
Audit trail lengkap
Export PDF otomatis
API integration
💥 11. FINAL POSITIONING

Dengan fitur ini, sistem Anda berubah dari:

❌ Aplikasi presensi
menjadi
✅ Platform kontrol operasional lapangan