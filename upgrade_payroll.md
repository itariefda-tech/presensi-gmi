# Upgrade Payroll

## Latar Belakang

Rencana awal adalah menambahkan modul payroll baru sebagai produk terpisah. Setelah update kebijakan owner, pendekatan itu tidak dipakai. Payroll yang sudah ada di-upgrade menjadi payroll yang lebih lengkap, tetap sebagai satu modul payroll.

Artinya:

- Tidak membuat modul payroll baru yang terpisah.
- Tidak membuat menu baru bernama Payroll Enterprise.
- Tidak memecah logic payroll menjadi dua produk berbeda.
- Payroll existing tetap menjadi pusat fitur.
- Fitur lanjutan ditambahkan bertahap sebagai upgrade payroll yang sudah ada.

Dokumen ini menyinkronkan rencana upgrade dengan kondisi aplikasi saat ini.

## Kondisi Payroll Saat Ini

Aplikasi sudah memiliki payroll dasar yang berjalan.

Komponen yang sudah ada:

- Tabel `payroll`.
- Generate payroll per employee dan periode.
- List payroll berdasarkan periode, status, client, site, dan scope user.
- Detail payroll.
- Update adjustment payroll untuk `potongan_lain` dan `tunjangan`.
- Approve payroll.
- Export payroll.
- Payroll di admin dashboard.
- Payroll di client dashboard.
- Integrasi dengan attendance summary.
- Payroll scheme:
  - `PRORATED_ATTENDANCE`
  - `FULL_MONTHLY_DEDUCTION`
- Payroll schedule:
  - `MONTH_END`
  - `MID_MONTH`
- Policy site/client sudah mengikat scheme dan schedule payroll.

Kolom payroll yang sudah tersedia antara lain:

- `employee_id`
- `client_id`
- `site_id`
- `branch_id`
- `employee_email`
- `period`
- `salary_base`
- `attendance_days`
- `working_days`
- `late_days`
- `absent_days`
- `leave_days`
- `daily_rate`
- `gross_salary`
- `potongan_telat`
- `potongan_absen`
- `late_deduction_rate`
- `absent_deduction_rate`
- `potongan_lain`
- `tunjangan`
- `total_gaji`
- `period_start`
- `period_end`
- `pay_date`
- `policy_id`
- `payroll_schedule`
- `payroll_scheme`
- `calculation_version`
- `status`
- `approved_by_email`
- `approved_at`
- `created_at`
- `updated_at`

## Hal Yang Tidak Dipakai Dari Rencana Lama

Beberapa bagian dari dokumen lama tidak berlaku untuk kondisi aplikasi saat ini.

Tidak berlaku:

- Membuat modul baru `payroll_enterprise`.
- Membuat blueprint baru khusus enterprise.
- Membuat menu baru `Payroll Enterprise`.
- Memisahkan payroll standard dan enterprise sebagai dua area produk.
- Membuat fitur API-ready untuk mobile app sebagai target saat ini.
- Membahas subscription, API subscription, API package, atau external API billing.
- Menggunakan konsep owner subscription sebagai dependency payroll.

Aplikasi saat ini belum masuk area API/subscription. Karena itu semua rencana yang terkait API/subscription tidak dimasukkan ke roadmap upgrade payroll ini.

## Arah Upgrade

Payroll existing akan diubah menjadi Payroll Engine yang lebih modular dan lengkap.

Target utamanya:

- Semua kalkulasi payroll melewati engine yang sama.
- Existing payroll tetap backward compatible.
- UI payroll tetap memakai halaman payroll yang sudah ada.
- Client dashboard payroll tetap memakai halaman payroll yang sudah ada.
- Fitur advanced ditambahkan sebagai field, breakdown, dan konfigurasi tambahan.
- Hasil payroll tetap tersimpan di tabel payroll existing, dengan tambahan kolom opsional jika diperlukan.

## Prinsip Arsitektur

1. Payroll existing tetap menjadi sumber utama.
2. Tidak ada duplikasi kalkulasi antara payroll lama dan payroll upgrade.
3. Kalkulasi payroll dipindah bertahap dari helper di `app.py` ke file engine khusus.
4. Semua output payroll harus punya breakdown yang jelas.
5. Semua field baru bersifat opsional agar data lama tetap valid.
6. Approval payroll lama tetap dipertahankan.
7. Generate payroll lama tetap berjalan walaupun field advanced belum diisi.

## Payroll Engine

Buat file baru:

```text
payroll_engine.py
```

Semua kalkulasi payroll diarahkan ke fungsi utama:

```python
run_payroll_engine(employee, attendance_summary, config)
```

Output minimal:

```python
{
    "gross": 0,
    "deductions": 0,
    "net": 0,
    "breakdown": {
        "basic_salary": 0,
        "allowances": {},
        "deductions": {},
        "bpjs": {},
        "tax": {},
        "thr": {},
        "overtime": {},
        "attendance": {}
    }
}
```

Fungsi kalkulasi yang perlu dipisah:

- `calculate_basic_salary()`
- `calculate_allowances()`
- `calculate_attendance_deductions()`
- `calculate_bpjs()`
- `calculate_tax_pph21()`
- `calculate_thr()`
- `calculate_overtime()`
- `calculate_custom_deductions()`
- `calculate_net_salary()`

## Cakupan Kalkulasi

Tidak perlu membuat produk berbeda. Payroll tetap satu modul, sementara engine internal menyesuaikan komponen yang tersedia pada slip.

### Dasar

Perhitungan dasar mempertahankan perilaku payroll saat ini:

- Basic salary.
- Prorated attendance atau full monthly deduction.
- Potongan telat.
- Potongan absen.
- Potongan lain.
- Tunjangan sederhana.
- Net salary atau `total_gaji`.

### Lengkap

Perhitungan lengkap menambahkan komponen payroll berikut:

- Allowance detail.
- Deduction detail.
- BPJS.
- PPh 21 sederhana.
- THR.
- Overtime.
- Breakdown payslip lengkap.

Komponen lengkap tidak menjadi menu atau tipe payroll baru. Komponen ini otomatis menjadi bagian dari payroll existing jika konfigurasinya tersedia.

## Komponen Payroll Yang Akan Ditambahkan

### 1. Allowances

Tambahkan struktur tunjangan yang lebih detail:

- Tunjangan jabatan.
- Tunjangan transport.
- Tunjangan makan.
- Tunjangan tetap.
- Tunjangan tidak tetap.
- Custom allowance.

Rekomendasi penyimpanan:

- Tetap gunakan `tunjangan` sebagai total allowance.
- Tambahkan field opsional `allowance_json` untuk breakdown.

### 2. Deductions

Deduction tetap mempertahankan field existing:

- `potongan_telat`
- `potongan_absen`
- `potongan_lain`

Tambahan yang disarankan:

- Custom deduction.
- Loan/cicilan karyawan jika nanti dibutuhkan.
- Penalty operasional jika disetujui.

Rekomendasi penyimpanan:

- Tetap gunakan `potongan_lain` sebagai total deduction tambahan.
- Tambahkan field opsional `deduction_json` untuk breakdown.

### 3. BPJS

Tambahkan kalkulasi BPJS sebagai fitur advanced.

Komponen:

- BPJS Kesehatan employee portion.
- BPJS Kesehatan company portion.
- BPJS Ketenagakerjaan JHT.
- BPJS Ketenagakerjaan JP.
- BPJS Ketenagakerjaan JKK.
- BPJS Ketenagakerjaan JKM.

Catatan:

- Nilai rate harus config-driven.
- Jangan hardcode rate di logic utama.
- Company portion perlu tampil di breakdown, tetapi tidak selalu mengurangi take-home pay.

### 4. PPh 21

Tambahkan kalkulasi PPh 21 sederhana.

Data yang dibutuhkan:

- PTKP status:
  - `TK0`
  - `TK1`
  - `K0`
  - `K1`
  - `K2`
  - `K3`
- Penghasilan bruto.
- Pengurang pajak.
- Estimasi pajak bulanan.

Catatan:

- Ini tahap awal menggunakan simplified monthly estimation.
- Jangan klaim sebagai final tax filing.
- Semua angka threshold dan rate harus config-driven.

### 5. THR

Tambahkan THR sebagai komponen advanced.

Aturan:

- Jika masa kerja >= 12 bulan, THR bisa 1x gaji pokok atau sesuai config.
- Jika masa kerja < 12 bulan, THR prorate.
- Manual override harus tersedia.

THR sebaiknya tidak otomatis masuk payroll bulanan kecuali periode tersebut ditandai sebagai periode THR.

### 6. Overtime

Tambahkan overtime berbasis jam.

Data:

- Total jam lembur.
- Rate lembur.
- Multiplier.
- Manual adjustment.

Sumber data overtime bisa disiapkan bertahap. Jika belum ada modul overtime, field manual di payroll profile atau form generate sudah cukup untuk fase awal.

## Database Upgrade

Jangan mengganti tabel payroll existing secara agresif.

Tambahkan kolom opsional secara bertahap:

```text
payroll_profile_id INTEGER
tax_status TEXT
bpjs_enabled INTEGER DEFAULT 0
allowance_json TEXT
deduction_json TEXT
bpjs_json TEXT
tax_json TEXT
thr_json TEXT
overtime_json TEXT
breakdown_json TEXT
engine_version TEXT
payroll_mode TEXT DEFAULT 'standard'
```

Pertimbangkan tabel baru untuk profile payroll employee:

```text
payroll_employee_profiles
```

Isi yang disarankan:

- `id`
- `employee_id`
- `client_id`
- `site_id`
- `salary_base`
- `tax_status`
- `bpjs_enabled`
- `bpjs_kesehatan_enabled`
- `bpjs_tk_enabled`
- `default_allowance_json`
- `default_deduction_json`
- `overtime_rate`
- `thr_base_multiplier`
- `created_at`
- `updated_at`

Alasan profile dipisah:

- Salary dan status pajak bukan data slip per periode.
- Payroll record tetap menjadi snapshot hasil generate.
- Jika profile berubah bulan depan, payroll bulan lama tidak ikut berubah.

## UI Upgrade

Tidak membuat menu baru. Upgrade halaman payroll yang sudah ada.

### Admin Payroll

Tambahkan bertahap:

- Payroll profile per employee.
- Breakdown detail di modal.
- Advanced fields collapsible.
- Export dengan breakdown.
- Highlight net salary.

### Client Payroll

Client dashboard payroll tetap sederhana.

Tambahkan:

- Ringkasan total payroll.
- Tunjangan dan potongan yang lebih jelas.
- Detail slip dengan breakdown.
- Status approve.
- Export ringkas.

Advanced configuration sebaiknya tetap di admin/HR, bukan di client dashboard biasa.

## Payslip Output

Payslip harus punya struktur:

- Employee info.
- Period info.
- Attendance summary.
- Salary base.
- Allowances.
- Deductions.
- BPJS employee portion.
- BPJS company portion.
- Tax.
- THR jika ada.
- Overtime jika ada.
- Gross salary.
- Total deductions.
- Net salary.
- Approval info.

Output awal cukup HTML/modal dan JSON internal. PDF bisa menjadi fase berikutnya.

## Security Dan Permission

Gunakan permission existing, jangan membuat sistem subscription baru.

Aturan:

- Admin/HR dengan permission payroll boleh generate payroll.
- Client admin hanya boleh melihat dan mengelola payroll sesuai scope client/site.
- Employee hanya boleh melihat payroll miliknya.
- Payroll approved tidak boleh diubah kecuali ada flow void/revision di masa depan.
- Semua perubahan payroll penting harus dicatat di audit log.

## Hal Yang Harus Tetap Kompatibel

Jangan merusak:

- `/api/payroll/generate`
- `/api/payroll/list`
- `/api/payroll/my`
- `/api/payroll/<id>`
- `/api/payroll/<id>/update`
- `/api/payroll/<id>/approve`
- Tabel payroll existing.
- Payroll scheme dan payroll schedule yang sudah mengikat di policy/site.
- UI payroll di admin dashboard.
- UI payroll di client dashboard.

## Tahapan Implementasi

### Fase 1 - Extract Engine

- Buat `payroll_engine.py`.
- Pindahkan logic `_calculate_payroll()` ke engine tanpa mengubah hasil.
- Tambahkan test yang membandingkan hasil engine dengan kalkulasi lama.
- Pastikan generate payroll existing tetap menghasilkan nilai sama.

### Fase 2 - Breakdown JSON

- Tambahkan `breakdown_json` dan `engine_version`.
- Simpan breakdown hasil kalkulasi.
- Tampilkan breakdown di modal detail payroll.
- Tetap isi field lama seperti `total_gaji`, `potongan_telat`, `potongan_absen`, dan `tunjangan`.

### Fase 3 - Payroll Employee Profile

- Tambahkan tabel payroll profile.
- Tambahkan UI profile payroll employee.
- Default profile boleh mengambil salary base dari input generate untuk menjaga kompatibilitas.
- Tambahkan tax status dan BPJS flag, tetapi belum wajib dipakai.

### Fase 4 - Allowance Dan Deduction Detail

- Tambahkan `allowance_json` dan `deduction_json`.
- UI breakdown allowance/deduction.
- Total tetap tersinkron ke `tunjangan` dan `potongan_lain`.

### Fase 5 - BPJS

- Tambahkan config BPJS.
- Tambahkan kalkulasi BPJS di engine.
- Simpan hasil di `bpjs_json`.
- Tampilkan employee portion dan company portion.

### Fase 6 - PPh 21 Sederhana

- Tambahkan config PTKP dan tax bracket.
- Tambahkan kalkulasi pajak bulanan.
- Simpan hasil di `tax_json`.
- Tampilkan disclaimer sebagai estimasi.

### Fase 7 - THR Dan Overtime

- Tambahkan THR prorate dan manual override.
- Tambahkan overtime manual/config-driven.
- Simpan hasil di `thr_json` dan `overtime_json`.

### Fase 8 - Export Dan Payslip

- Rapihkan payslip detail.
- Export CSV/Excel lebih lengkap.
- Siapkan struktur data future PDF tanpa harus langsung membuat PDF.

## Catatan Penting

Upgrade ini harus dilakukan bertahap. Jangan langsung memasukkan seluruh fitur BPJS, pajak, THR, dan overtime dalam satu perubahan besar.

Prioritas pertama adalah membuat payroll engine yang rapi dan menjaga hasil payroll existing tetap sama. Setelah engine stabil, baru komponen advanced ditambahkan satu per satu.

## Status Implementasi

Status terakhir:

- Fase 1 Extract Engine sudah berjalan melalui `payroll_engine.py`.
- Fase 2 Breakdown JSON sudah tersimpan melalui `breakdown_json` dan `engine_version`.
- Fase 3 Payroll Employee Profile sudah tersedia melalui tabel `payroll_employee_profiles` dan endpoint `/api/payroll/profile`.
- Fase 4 Allowance dan Deduction Detail sudah tersimpan sebagai `allowance_json` dan `deduction_json`.
- Fase 5 BPJS sudah berjalan: rate dan cap BPJS dibuat config-driven, payroll dengan `bpjs_enabled` berjalan dalam mode `advanced`, hasil BPJS tersimpan di `bpjs_json`, dan breakdown menampilkan porsi employee serta company.
- Fase 6 PPh 21 sederhana sudah berjalan: status PTKP dari payroll profile mengaktifkan estimasi PPh21 annualized, config PTKP/bracket bersifat overrideable, hasil estimasi tersimpan di `tax_json`, dan breakdown membawa disclaimer estimasi.
- Fase 7 THR dan Overtime sudah berjalan untuk input manual/generate: THR mendukung periode THR, prorate masa kerja, manual override, overtime mendukung jam, rate, multiplier, dan manual override. Hasil tersimpan di `thr_json` dan `overtime_json`.
- Fase 8 Export dan Payslip sudah dimulai: detail payslip/modal memakai breakdown engine, export payroll admin/client sudah membawa kolom BPJS, PPh21, THR, overtime, gross, dan net. PDF belum dibuat.
- Follow-up UI audit sudah dikerjakan: admin payroll memiliki KPI payroll lengkap, filter jenis payroll sudah dihapus, form konfigurasi payroll collapsible, tabel utama menampilkan komponen earning/deduction/statutory, client payroll insight sudah data-driven, dan detail client tampil sebagai slip breakdown.
- Follow-up security/data audit sudah dikerjakan sebagian: `payroll_profile_id` tersimpan sebagai referensi snapshot, generate/profile/update adjustment payroll dicatat ke audit log. PDF dan konfigurasi rate/tax dari halaman settings masih future enhancement.

## Ringkasan Keputusan

Keputusan final:

- Payroll existing di-upgrade.
- Tidak ada modul Payroll Enterprise terpisah.
- Tidak ada menu baru Payroll Enterprise.
- Tidak membahas API/subscription.
- Payroll hanya satu modul: HRIS Pro bisa berjalan tanpa payroll, dan payroll aktif saat owner menyalakan add-on Payroll.
- Semua fitur advanced harus backward compatible dan config-driven.
