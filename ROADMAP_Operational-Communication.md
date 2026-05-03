# 🧠 HRIS GMI — Operational Communication System Roadmap

Fitur ini bukan sekadar chat.
Ini adalah layer komunikasi operasional terstruktur untuk sistem outsource:
- Koordinasi real-time
- Announcement terkontrol
- Incident berbasis event
- Audit komunikasi

## Status Pencapaian Saat Ini

Sampai titik ini, layer operational communication sudah melewati fondasi basic chat dan sudah masuk mode usable untuk operasional:

- room komunikasi `private`, `site`, `role`, `incident`, dan `shift` sudah hidup
- announcement, incident reporting, dan thread discussion sudah tersedia
- polling notification, sound, dan vibration dasar sudah berjalan
- hardening dasar sudah aktif: rate limit, audit trail, duplicate throttle, scope validation
- fitur communication sekarang difokuskan ke tiga layer inti: live chat, announcement, dan incident system
- owner credential modal sekarang menjadi perintah induk untuk fitur komunikasi

Catatan paket:

- `HRIS Pro` tidak otomatis membuka seluruh layer communication enterprise
- `HRIS Pro Plus` mengikuti add-on yang diaktifkan satu per satu
- `HRIS Enterprise` membuka keseluruhan layer communication yang sudah tersedia, kecuali item roadmap yang memang masih belum dicentang

---

# 🎯 OBJECTIVE

- Menggantikan komunikasi liar (WhatsApp)
- Menyediakan komunikasi berbasis role & site
- Menyimpan jejak komunikasi (audit trail)
- Meningkatkan kontrol operasional

---

# 🧱 PHASE 1 — FOUNDATION (BASIC CHAT & STRUCTURE)

## Database
- [x] Buat tabel `messages`
  - id
  - sender_email
  - receiver_type (user / role / site)
  - receiver_id (email / role_name / site_id)
  - message
  - created_at
  - is_read

- [x] Buat tabel `chat_rooms`
  - id
  - type (private / role / site)
  - name
  - created_at

- [x] Relasi `message -> chat_room`

---

## Backend (Flask API)
- [x] Endpoint kirim pesan
  - `POST /api/chat/send`

- [x] Endpoint ambil pesan per room
  - `GET /api/chat/room/<id>`

- [x] Endpoint list chat user
  - `GET /api/chat/list`

---

## Frontend
### Dashboard Pegawai
- [x] Tambah menu: "Chat"
- [x] UI chat sederhana (bubble kiri-kanan)
- [x] Input message + send button

### Dashboard Admin
- [x] Monitoring chat basic (read-only)

---

## Behavior
- [x] Employee hanya bisa chat:
  - supervisor
  - site group

- [x] Supervisor bisa chat:
  - employee
  - koordinator

### Implementasi Phase 1
- [x] Fondasi chat sekarang aktif dengan room `private`, `site`, dan `role`.
- [x] Employee dashboard punya pane komunikasi untuk room chat dan pengumuman.
- [x] Admin settings punya tab monitoring komunikasi read-only.

---

# 🚀 PHASE 2 — ROLE & SITE BASED COMMUNICATION

## Backend
- [x] Filtering chat berdasarkan:
  - role
  - site/client

- [x] Auto-create room:
  - site room
  - role room

---

## Frontend
- [x] Tab chat:
  - [x] Private
  - [x] Site
  - [x] Role

- [x] Badge unread count

---

## Feature
- [x] Read status (dibaca)
- [x] Last message preview

### Implementasi Phase 2
- [x] List room chat sekarang mengikuti scope akses user dan otomatis membentuk room default sesuai site/role.
- [x] Unread count dan preview pesan terakhir tampil di daftar room pegawai.

---

# 📢 PHASE 3 — ANNOUNCEMENT SYSTEM

## Database
- [x] Tabel `announcements`
  - id
  - title
  - message
  - target_type (global / role / site)
  - target_id
  - created_by
  - created_at
  - expired_at
  - is_mandatory

- [x] Tabel `announcement_reads`
  - user_email
  - announcement_id
  - read_at

---

## Backend
- [x] `POST /api/announcement/create`
- [x] `GET /api/announcement/list`
- [x] `POST /api/announcement/read`

---

## Frontend
### Admin
- [x] Form create announcement
- [x] Pilih target (role/site/global)

### Employee
- [x] Panel "Pengumuman"
- [x] Highlight jika mandatory

---

## Feature
- [x] Tracking siapa sudah baca
- [ ] Mandatory read blocking (opsional)
- [x] Badge notif

### Implementasi Phase 3
- [x] Admin dapat publish pengumuman global, role, atau site dari tab Communication.
- [x] Employee dapat melihat pengumuman yang sesuai scope dan menandainya sebagai sudah dibaca.

---

# 🚨 PHASE 4 — INCIDENT COMMUNICATION (GAME CHANGER)

## Database
- [x] Tabel `incidents`
  - id
  - title
  - description
  - photo_path
  - site_id
  - created_by
  - created_at
  - status (open / closed)

- [x] Link ke chat_room (auto thread)

---

## Backend
- [x] `POST /api/incident/create`
- [x] `GET /api/incident/list`
- [x] Auto-create chat room per incident

---

## Frontend
- [x] Button: "Laporkan Kejadian"
- [x] Form upload foto + deskripsi
- [x] Auto masuk ke chat incident

---

## Behavior
- [x] Supervisor auto-notified
- [x] Incident punya chat sendiri

### Implementasi Phase 4
- [x] Employee dashboard sekarang punya form incident lengkap dengan upload foto opsional.
- [x] Setiap incident otomatis membuat room chat sendiri dan mengirim pesan pembuka ke room tersebut.
- [x] Supervisor/admin yang punya scope site/client terkait bisa melihat feed incident dan room-nya.

---

# 🧵 PHASE 5 — THREAD DISCUSSION

## Database
- [x] Tambah `thread_id` di messages

- [x] Tabel `threads`
  - id
  - title
  - created_by
  - created_at
  - is_locked

---

## Backend
- [x] Create thread
- [x] Reply thread
- [x] Lock thread

---

## Frontend
- [x] UI thread (mirip forum)
- [x] Group message per topic

### Implementasi Phase 5
- [x] Room chat sekarang punya panel thread diskusi dengan daftar topik, tombol buat thread, dan reply per topik.
- [x] Pesan di employee dashboard bisa difilter per thread sehingga alur diskusi lebih rapi seperti forum ringan.

---

# 🔐 PHASE 6 — HARDENING & CONTROL

## Rules
- [x] Role-based access chat
- [x] Limit cross-role messaging
- [x] Anti spam basic

---

## Audit
- [x] Log semua aktivitas:
  - [x] send message
  - [x] read
  - [x] delete

- [x] Admin audit panel

---

## Security
- [x] Sanitasi input message
- [x] Limit file upload
- [x] Rate limit endpoint chat

### Implementasi Phase 6
- [x] Scope akses room sekarang dibatasi per private/site/role/incident sehingga cross-role tidak liar.
- [x] Chat send punya anti-spam dan duplicate throttle dasar untuk menahan flood.
- [x] Admin settings tab Communication menampilkan audit trail komunikasi dan incident monitoring.

---

# 💎 PHASE 7 — ADVANCED (ENTERPRISE LEVEL)

## Smart System
- [ ] Escalation:
  - jika tidak dibalas → naik ke atasan

- [ ] Auto-routing:
  - berdasarkan struktur organisasi

---

## Context Awareness
- [x] Chat berdasarkan shift
- [ ] Chat berdasarkan lokasi (geo)

---

## Notification
- [x] Real-time notif (websocket / polling)
- [x] Sound / vibration (mobile)

### Implementasi Phase 7
- [x] Employee dashboard melakukan polling berkala untuk room chat, pengumuman, dan incident.
- [x] Saat ada update baru, UI memunculkan toast dan trigger vibration pada device yang mendukung.
- [x] Room shift otomatis dibuat dari assignment aktif sehingga koordinasi per shift punya channel sendiri.

---

# 🔌 ADD-ON SYSTEM (TIER CONTROL)

## Feature Flag (PENTING)
- [x] Tambah field di user / tenant:
  - [x] `communication_enabled`
  - [x] `tier_level` (pro / pro_plus / enterprise)

---

## Toggle di Owner Panel
- [x] Modal: Credential Owner

Tambahkan:
- [x] Toggle:
  - [x] Enable Chat
  - [x] Enable Announcement
  - [x] Enable Incident System

- [x] Dropdown Tier:
  - [x] Pro
  - [x] Pro Plus
  - [x] Enterprise

---

## Behavior Tier

### PRO
- [x] Chat private
- [x] Chat site

### PRO PLUS
- [x] + Announcement
- [x] + Read tracking

### ENTERPRISE
- [x] + Incident system
- [x] + Thread discussion
- [ ] + Escalation

### Implementasi Add-on System
- [x] Owner panel sekarang punya toggle global untuk chat, announcement, dan incident system.
- [x] Konfigurasi per client tersedia di tab Communication untuk enable/disable komunikasi, pilih tier, serta atur limit pesan dan attachment.
- [x] Gating fitur sudah mengikuti tier: Pro untuk chat, Pro Plus menambah announcement, Enterprise membuka incident dan thread.
- [x] Credential Owner menjadi perintah induk: saat toggle owner mematikan atau membatasi tier komunikasi, konfigurasi client dan endpoint otomatis mengikuti batas tersebut.
- [x] Layer mode aplikasi `HRIS Pro`, `HRIS Pro Plus`, dan `HRIS Enterprise` sekarang ikut membatasi perilaku add-on komunikasi dari level owner.

---

# 🔐 HARDENING INTEGRATION

## Hardening
- [x] Rate limit:
  - [x] chat send
  - [x] upload

- [x] Role validation di setiap endpoint

---

## Credential Owner Panel
Tambahkan:
- [x] Limit:
  - [x] message/day
  - [x] attachment size

### Implementasi Hardening Integration
- [x] Endpoint komunikasi sekarang kembali murni mengikuti session login dan tier communication owner/client, tanpa kaitan API access.
- [x] Rate limit harian pesan dan limit ukuran attachment incident mengikuti konfigurasi komunikasi per client.

---

# 🧪 PHASE 8 — TESTING & STABILITY

- [x] Test antar role
- [x] Test multi-site
- [ ] Test load chat
- [x] Test incident flow

### Implementasi Phase 8
- [x] Test mencakup employee, supervisor, dan hr superadmin.
- [x] Multi-site isolation sudah diuji agar incident/chat tidak bocor ke site lain.
- [x] Incident flow end-to-end dan rate limit chat dasar sudah masuk regression suite.

---

# 🏁 FINAL GOAL

- HRIS bukan hanya presensi
- Tapi:
  ✅ alat komunikasi kerja
  ✅ alat kontrol operasional
  ✅ sistem audit komunikasi
