==================================================
PHASE 15 - CONTRACT, SLA & BILLING (ENTERPRISE)
==================================================

Goal:
- Enable monetization (billing-ready)
- Support enterprise client contract
- Flexible pricing via tier + add-on toggle

Scope:
- ONLY aktif jika:
  package = ENTERPRISE
  AND addon_billing = ENABLED

--------------------------------------------------
SECTION 1 - PACKAGE & ADD-ON CONTROL
--------------------------------------------------

Objective:
- Feature bisa diaktifkan / dimatikan oleh Owner
- Tidak mengganggu client non-enterprise

Data Model:

table: client_packages
- id
- client_id
- package_type (BASIC / PRO / ENTERPRISE)
- is_active

table: client_addons
- id
- client_id
- addon_key (BILLING, SLA, CONTRACT)
- is_enabled (boolean)

Addon Keys:
- BILLING_ENGINE
- CONTRACT_MANAGEMENT
- SLA_TRACKING

Rules:
- Billing hanya jalan jika:
  package = ENTERPRISE
  AND BILLING_ENGINE = true

--------------------------------------------------
SECTION 2 - CLIENT CONTRACT MANAGEMENT
--------------------------------------------------

Objective:
- Menyimpan kontrak client sebagai acuan sistem

table: client_contracts
- id
- client_id
- contract_no
- start_date
- end_date
- notice_period_days
- scope_summary (text)
- sla_summary (text)
- is_active

Optional:
- payroll_cycle_type (END_MONTH / MID_MONTH)
- payroll_cutoff_day (16 / 30)

Logic:
- 1 client bisa punya multiple contract (history)
- hanya 1 contract aktif

Usage:
- attendance & payroll refer ke contract aktif

--------------------------------------------------
SECTION 3 - BILLING CONFIGURATION
--------------------------------------------------

Objective:
- Menentukan cara hitung biaya

table: billing_configs
- id
- client_id
- billing_type (PER_HEAD / PER_SITE / PER_SHIFT)
- rate
- tax_percent
- payment_terms_days
- invoice_email
- is_active

Logic:
- 1 active billing_config per client
- fallback: none (billing disable jika tidak ada config)

--------------------------------------------------
SECTION 4 - BILLING DATA AGGREGATOR
--------------------------------------------------

Objective:
- Mengubah data operasional → data siap tagih

Source:
- attendance
- employees
- sites

Aggregator Output (virtual / materialized):

billing_summary:
- client_id
- period (YYYY-MM)
- total_employees
- total_sites
- total_attendance
- total_shifts
- calculated_amount

Rules:
- PER_HEAD → total_employees * rate
- PER_SITE → total_sites * rate
- PER_SHIFT → total_attendance * rate

--------------------------------------------------
SECTION 5 - READ-ONLY BILLING DASHBOARD
--------------------------------------------------

Objective:
- Transparansi ke owner / finance

Dashboard Cards:
- Active Contract
- Billing Type
- Estimated Monthly Cost
- Usage Breakdown

Views:
- summary per month
- detail per site / employee (optional)

NOTE:
- NO invoice generation yet (phase berikutnya)

--------------------------------------------------
SECTION 6 - INTEGRATION TO CORE MODULE
--------------------------------------------------

Attendance:
- supply total attendance
- supply shift data

Payroll:
- optional reference (employee count)

Site:
- supply active site count

IMPORTANT:
- TIDAK mengubah flow existing
- hanya read + aggregate

--------------------------------------------------
SECTION 7 - OWNER CONTROL (UI/UX)
--------------------------------------------------

Objective:
- Owner bisa toggle fitur dari 1 tempat

Menu:
Settings → Subscription / Package

UI:
- Select Package:
  [ BASIC | PRO | ENTERPRISE ]

- Add-ons (checkbox / toggle):
  [ ] Contract Management
  [ ] SLA Tracking
  [ ] Billing Engine

Behavior:
- Toggle OFF:
  → semua fitur billing hide
  → data tetap tersimpan (soft disable)

- Toggle ON:
  → fitur aktif kembali

--------------------------------------------------
SECTION 8 - ACCESS CONTROL
--------------------------------------------------

Roles:
- OWNER → full access
- FINANCE → read billing
- ADMIN → no access (default)

Permission:
- billing.view
- billing.config.update
- contract.manage

--------------------------------------------------
SECTION 9 - SAFETY & FALLBACK
--------------------------------------------------

If:
- addon OFF → skip semua logic billing
- contract tidak ada → tampil warning
- billing_config tidak ada → no calculation

--------------------------------------------------
OUTCOME
--------------------------------------------------

✔ HRIS siap untuk enterprise client
✔ Monetization model fleksibel
✔ Bisa scaling ke multi-client billing
✔ Tidak mengganggu client existing