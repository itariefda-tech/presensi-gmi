# HRIS GMI - Audit Notes & Technical Debt

Dokumen ini merangkum kondisi teknis untuk menjaga konsistensi sistem.
Fokus: storage, alur utama, dan technical debt.

## Ringkasan Kondisi

| Area | Status | Catatan |
| --- | --- | --- |
| Auth (Login/Signup/Forgot) | REAL | Users & roles tersimpan SQLite |
| Attendance (Checkin/Checkout) | REAL | SQLite `attendance` |
| Manual Attendance | REAL | SQLite `manual_attendance_requests` |
| Leave Management | REAL | SQLite `leave_requests` |
| Approvals Page | REAL | Leave + Manual di SQLite |

Kesimpulan: flow end-to-end berjalan, tapi storage masih campuran.

## Flow Map (Ringkas)

1) Auth  
- UI: `index.html` (tidak diubah)  
- API: `/api/auth/*`  
- Storage: SQLite `users`

2) Attendance  
- UI: `employee.html`  
- API: `/api/attendance/checkin|checkout`  
- Storage: SQLite `attendance`

3) Manual Attendance  
- UI: `/dashboard/manual_attendance`  
- Approval: `/dashboard/admin/manual_attendance/<id>/approve|reject`  
- Storage: SQLite

4) Leave  
- UI: `employee.html`  
- API: `/api/leave/*`  
- Storage: SQLite `leave_requests`

## Risiko Utama (Jika Dibiarkan)
- Data retention dan indexing masih perlu ditinjau

## Rekomendasi Berikutnya (Post Demo)
- Role + assignment berbasis site
- Indexing + retention policy

Dokumen ini sengaja terpisah dari README untuk menjaga roadmap tetap ringkas.
