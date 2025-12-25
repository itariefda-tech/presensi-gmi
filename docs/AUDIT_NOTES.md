# HRIS GMI - Audit Notes & Technical Debt

Dokumen ini merangkum kondisi teknis untuk menjaga konsistensi demo.
Fokus: membedakan REAL (SQLite) dan DEMO (in-memory).

## Ringkasan Kondisi

| Area | Status | Catatan |
| --- | --- | --- |
| Auth (Login/Signup/Forgot) | REAL | Users & roles tersimpan SQLite |
| Attendance (Checkin/Checkout) | DEMO | Data hilang saat restart |
| Manual Attendance | REAL | SQLite `manual_attendance_requests` |
| Leave Management | DEMO | In-memory |
| Approvals Page | MIXED | Leave DEMO, Manual REAL |

Kesimpulan: flow end-to-end berjalan, tapi storage masih campuran.

## Flow Map (Ringkas)

1) Auth  
- UI: `index.html` (tidak diubah)  
- API: `/api/auth/*`  
- Storage: SQLite `users`

2) Attendance  
- UI: `employee.html`  
- API: `/api/attendance/checkin|checkout`  
- Storage: DEMO `DEMO_ATTENDANCE`

3) Manual Attendance  
- UI: `/dashboard/manual_attendance`  
- Approval: `/dashboard/admin/manual_attendance/<id>/approve|reject`  
- Storage: SQLite

4) Leave  
- UI: `employee.html`  
- API: `/api/leave/*`  
- Storage: DEMO `DEMO_LEAVE_REQUESTS`

## Risiko Utama (Jika Dibiarkan)
- Attendance/leave hilang saat restart
- Approvals masih campur DEMO/SQLite

## Rekomendasi Berikutnya (Post Demo)
- Migrasi attendance ke SQLite
- Migrasi leave ke SQLite
- Role + assignment berbasis site

Dokumen ini sengaja terpisah dari README untuk menjaga roadmap tetap ringkas.
