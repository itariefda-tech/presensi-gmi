# API Spec Enterprise

Dokumen ini merangkum endpoint enterprise yang sudah tersedia dan cara mengaktifkan `API access` untuk integrasi eksternal.

## Auth

- `POST /api/auth/login`
  - Body: `identifier`, `email`, atau `phone`, `password`, `login_type`
  - Security: persistent rate limit via `login_attempts`
- `POST /api/auth/forgot`
- `POST /api/auth/reset_password`

## Attendance

- `POST /api/attendance/checkin`
- `POST /api/attendance/checkout`
- `GET /api/attendance/today`
- `GET /api/attendance/summary`
- `POST /api/attendance/manual`
- `POST /api/attendance/approve`
- `POST /api/attendance/reject`
- `GET /api/v1/attendance`
  - Kegunaan: endpoint integrasi untuk menarik data attendance per client
  - Auth:
    - `X-API-Key: <token>`
    - atau `Authorization: Bearer <token>`
  - Query:
    - `client_id` wajib untuk legacy token/global admin flow
    - `site_id` opsional, tetapi harus milik client yang sama
    - `employee_email` opsional, tetapi harus tetap berada dalam scope client/site
    - `from` dan `to` opsional dalam format `YYYY-MM-DD`
    - `limit` opsional, default `200`, maksimal `1000`
  - Response sukses:

```json
{
  "ok": true,
  "data": {
    "client_id": 1,
    "site_id": 1,
    "branch_id": 1,
    "employee_email": "emp1@acme.test",
    "date_from": "2026-04-10",
    "date_to": "2026-04-10",
    "records": []
  }
}
```

## Reports

- `GET /api/reports/attendance`
- `GET /api/reports/late`
- `GET /api/reports/absent`
- `GET /api/reports/summary`

## Leave

- `POST /api/leave/create`
- `POST /api/leave/request`
- `GET /api/leave/my`
- `GET /api/leave/pending`
- `POST /api/leave/approve`
- `POST /api/leave/reject`

## Payroll

- `POST /api/payroll/generate`
- `GET /api/payroll/history`
- `POST /api/payroll/approve`
- `GET /api/payroll/export`

## Owner & Settings

- `GET /api/owner/addons`
- `POST /api/owner/addons/verify`
- `POST /api/owner/addons`
- `POST /dashboard/admin/settings/subscription/update`
- `POST /dashboard/admin/settings/subscription/<client_id>/api-access/token`
- `POST /dashboard/admin/settings/subscription/<client_id>/api-access/token/<token_id>/revoke`

## Enterprise Billing & Contract

- `POST /dashboard/admin/clients/<client_id>/contract/save`
- `POST /dashboard/admin/clients/<client_id>/billing/save`
- Read-only billing summary is rendered in Client Profile.

## Mengaktifkan API access

1. Buka owner add-on dan aktifkan `API access`.
2. Buka `Dashboard Admin -> Settings -> Subscription`.
3. Pilih client target dan set package ke `Enterprise`.
4. Centang add-on `API access` lalu simpan.
5. Pada panel `API Credentials`, generate token baru dengan label integrasi.
6. Gunakan token itu dari sistem eksternal melalui `X-API-Key` atau `Authorization: Bearer`.

Catatan:
- `API access` tidak otomatis aktif hanya karena bundle `Enterprise`.
- Toggle owner/global hanya membuka ketersediaan fitur.
- Aktivasi nyata tetap dilakukan per client.

## Contoh Request API Dengan Token

```bash
curl -X GET "https://example.com/api/v1/attendance?client_id=1&site_id=1&from=2026-04-10&to=2026-04-10&limit=100" ^
  -H "X-API-Key: gmi_your_generated_token"
```

Contoh dengan `employee_email`:

```bash
curl -X GET "https://example.com/api/v1/attendance?client_id=1&employee_email=emp1@acme.test&from=2026-04-10&to=2026-04-10" ^
  -H "Authorization: Bearer gmi_your_generated_token"
```

## Contoh Error

Add-on belum aktif pada client:

```json
{
  "ok": false,
  "message": "API access add-on belum aktif."
}
```

Token tidak valid:

```json
{
  "ok": false,
  "message": "Token API tidak valid."
}
```

`client_id` tidak dikirim:

```json
{
  "ok": false,
  "message": "client_id wajib untuk API access."
}
```

Site bukan milik client:

```json
{
  "ok": false,
  "message": "branch_id tidak terdaftar pada client ini."
}
```

Quota harian tercapai:

```json
{
  "ok": false,
  "message": "Limit harian API access tercapai."
}
```

## Rotate / Revoke Token

- Token disimpan sebagai hash di database, bukan plaintext.
- Plaintext token hanya tampil sekali saat generate.
- Untuk rotate token:
  - generate token baru
  - update konfigurasi di sistem integrasi
  - revoke token lama setelah integrasi pindah
- Untuk revoke token:
  - buka panel `API Credentials`
  - klik `Revoke` pada token target
  - token langsung tidak bisa dipakai lagi
- Jika add-on `API access` pada client dimatikan:
  - token lama tetap tersimpan
  - semua request API client itu tetap ditolak sampai add-on diaktifkan lagi

## Security Notes

- Form POST uses CSRF token.
- JSON POST uses `X-CSRF-Token` or `csrf_token` body when a session user exists.
- API access routes use add-on gating where applicable.
- Token per client dibatasi oleh scope client dan validasi site/employee.
- Audit log dibuat saat token generate/revoke dan saat request API penting masuk.
- Rate limit harian aktif untuk level token dan level client.
