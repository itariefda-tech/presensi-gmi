# Output Roadmap Patroli Notes & Report

Sumber acuan: `roadmap_patroli-notes-report.md`

Status pengerjaan: Phase 1 sampai Phase 3 diimplementasikan sebagai MVP bertahap tanpa mengubah arsitektur utama project.

## Phase 1 - Core MVP

- [x] Activity Log pegawai tersedia di dashboard mobile.
- [x] Gate Log pegawai tersedia dengan arah masuk/keluar, plat nomor, jenis kendaraan, catatan, foto opsional.
- [x] Auto capture data dasar: timestamp, employee, assignment, client, site.
- [x] GPS dikirim bila sudah tersedia dari device/patrol state.
- [x] Foto aktivitas tersimpan melalui upload `static/uploads/patrol_notes`.
- [x] Data disimpan ke SQLite lewat tabel `patrol_operational_events`.
- [x] Timeline aktivitas pegawai tersedia lewat `/api/patrol/notes/timeline`.

## Phase 2 - Incident & Handover

- [x] Incident Report tersedia di dashboard pegawai.
- [x] Incident memiliki severity `low`, `warning`, `critical`.
- [x] Deskripsi insiden wajib diisi dari server-side validation.
- [x] Handover tersedia dengan checklist pintu, CCTV, listrik.
- [x] Handover mendukung catatan tambahan dan foto kondisi.
- [x] Supervisor/client dapat menambahkan `supervisor_note`.
- [x] Status aktivitas dapat diubah menjadi `reviewed` atau `resolved`.

## Phase 3 - Patrol Tracking, Live Activity, Report Dasar

- [x] Guard Tour existing tetap digunakan untuk checkpoint, scan, strict mode, GPS, selfie, dan rekap sesi.
- [x] Client dashboard memiliki panel `Live Activity & Notes`.
- [x] Feed notes dapat difilter berdasarkan kategori: activity, gate, incident, handover.
- [x] Client dashboard menampilkan nama pegawai, waktu, severity/status, plat kendaraan, catatan, dan supervisor note.
- [x] Endpoint client live/report tersedia melalui `/api/client/patrol/notes`.
- [x] Endpoint validasi status tersedia melalui `/api/client/patrol/notes/update`.
- [x] Report Guard Tour existing tetap tersedia melalui `/api/admin/guard_tour/report` dan dashboard guard tour.

## Phase 4 - Belum Dikerjakan Penuh

- [x] Internal notification untuk critical incident ke client user site dan admin operasional.
- [ ] WhatsApp/Telegram alert.
- [ ] WebSocket realtime; saat ini masih polling/refresh.
- [ ] Client portal eksternal khusus pelanggan.
- [x] Export CSV report notes dari dashboard client.
- [ ] Export PDF otomatis.
- [ ] Performance scoring/KPI otomatis.
- [ ] AI insight/photo verification.
- [x] Ringkasan analytics dasar notes: total, critical, open, resolved.

## Phase 5 - Performance Scoring MVP

- [x] Endpoint performance scoring tersedia untuk dashboard client.
- [x] Skor pegawai dihitung dari completion checkpoint, jumlah aktivitas, handover, incident, critical incident, dan open issue.
- [x] Dashboard client menampilkan Top Performer, average score, dan jumlah pegawai yang butuh perhatian.
- [x] Ranking pegawai tersedia dengan badge `Excellent`, `Good`, `Perlu Dipantau`, dan `Risk`.
- [x] Metric pendukung ditampilkan: checkpoint done/total, activity count, incident count, open issue.
- [ ] Formula KPI final belum dikunci sebagai policy enterprise.
- [ ] Scoring belum masuk payroll/SLA/report PDF.

## Phase 6 - SLA Reporting MVP

- [x] Endpoint SLA patrol tersedia untuk dashboard client.
- [x] SLA harian dihitung dari completion checkpoint, missed checkpoint, critical incident, dan open issue.
- [x] Dashboard client menampilkan compliance rate, jumlah compliant, warning, dan breach.
- [x] Daftar SLA harian menampilkan sesi patrol, completion rate, checkpoint done/total, missed, critical, dan open issue.
- [x] Status SLA dasar tersedia: `Compliant`, `Warning`, `Breach`.
- [ ] Ambang SLA final belum dikunci sebagai kontrak enterprise.
- [ ] SLA belum terhubung ke invoice/SLA penalty/report PDF.

## Phase 7 - Admin Control Room Integration

- [x] Admin Guard Tour Control Center menampilkan operational notes per site.
- [x] Admin dapat filter kategori notes: activity, gate, incident, handover.
- [x] Admin dapat export operational notes CSV.
- [x] Admin dapat update status notes menjadi `reviewed` atau `resolved` dengan supervisor note.
- [x] Admin Guard Tour menampilkan Performance Ranking site terpilih.
- [x] Admin Guard Tour menampilkan SLA Daily site terpilih.
- [x] Endpoint admin dibuat untuk notes, performance, dan SLA Guard Tour.
- [ ] Tampilan admin belum memakai date quick preset.
- [x] Admin Control Room dapat membuka evidence foto dan lokasi dari operational notes.
- [ ] Admin Control Room belum punya modal detail evidence penuh.

## Phase 8 - Evidence Drilldown MVP

- [x] Client dashboard dapat membuka foto evidence dari operational notes.
- [x] Client dashboard dapat membuka koordinat evidence di Google Maps dari operational notes.
- [x] Admin Guard Tour dapat membuka foto evidence dari operational notes.
- [x] Admin Guard Tour dapat membuka koordinat evidence di Google Maps dari operational notes.
- [x] Evidence memakai data `photo_path`, `lat`, dan `lng` yang sudah tersimpan di `patrol_operational_events`.
- [ ] Belum ada preview modal inline.
- [ ] Belum ada gallery/evidence archive khusus per site.

## Endpoint Baru

- [x] `POST /api/patrol/notes/create`
- [x] `GET /api/patrol/notes/timeline`
- [x] `GET /api/client/patrol/notes`
- [x] `POST /api/client/patrol/notes/update`
- [x] `GET /api/client/patrol/notes/summary`
- [x] `GET /api/client/patrol/performance`
- [x] `GET /api/client/patrol/sla`
- [x] `GET /api/admin/guard_tour/notes`
- [x] `POST /api/admin/guard_tour/notes/update`
- [x] `GET /api/admin/guard_tour/performance`
- [x] `GET /api/admin/guard_tour/sla`

## Database Baru

- [x] `patrol_operational_events`
- [x] Index site + created_at
- [x] Index employee_email + created_at
- [x] Index category + status

## Validasi QA Singkat

- [x] Syntax Python valid.
- [x] Syntax JS employee dashboard valid.
- [x] Syntax JS client dashboard valid.
- [x] Role employee hanya bisa submit dan melihat timeline sendiri.
- [x] Role client hanya bisa melihat/update aktivitas pada site miliknya.
- [x] Perubahan tidak menambah library baru.
