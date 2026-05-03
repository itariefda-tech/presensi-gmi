You are working on an existing Flask-based HRIS system (attendance + leave system).
The system currently DOES NOT have payroll feature and must remain backward compatible.

Your task is to implement a NEW feature:
"Payroll Enterprise (Advanced Payroll System - Indonesia Compliance)"

IMPORTANT RULES:
- DO NOT modify or break existing payroll standard (if exists later)
- This must be a SEPARATE module: "payroll_enterprise"
- Must be ENABLED/DISABLED via OWNER CREDENTIAL toggle
- Follow modular, scalable, production-ready structure

--------------------------------------------------
🎯 FEATURE OVERVIEW
--------------------------------------------------

Create a new payroll system that includes:

1. Basic Salary (Gaji Pokok)
2. Allowances (Tunjangan):
   - Tunjangan Jabatan
   - Tunjangan Transport
   - Tunjangan Makan
   - Custom Allowance (dynamic)

3. Deductions (Potongan):
   - Absence deduction (alpha / no attendance)
   - Late penalty (optional)
   - Custom deduction

4. BPJS (Indonesia Compliance):
   - BPJS Kesehatan (Employee + Company portion)
   - BPJS Ketenagakerjaan:
     - JHT (Jaminan Hari Tua)
     - JP (Jaminan Pensiun)
     - JKK
     - JKM

5. TAX (PPh 21 simplified version):
   - Support PTKP status:
     - TK0, TK1, K0, K1, K2, K3
   - Progressive tax calculation (simplified)
   - Monthly estimation

6. THR (Tunjangan Hari Raya):
   - Auto prorate if < 12 months
   - Manual override allowed

7. Overtime:
   - Hour-based calculation
   - Configurable multiplier

--------------------------------------------------
🧱 DATABASE DESIGN
--------------------------------------------------

Create new tables:

- payroll_config
- payroll_employee_profile
- payroll_components
- payroll_runs
- payroll_run_details

Each employee must have:
- salary base
- tax status (PTKP)
- bpjs participation flag

--------------------------------------------------
⚙️ OWNER TOGGLE (CRITICAL)
--------------------------------------------------

Add new setting:

OWNER_ADDON_PAYROLL_ENTERPRISE = true/false

Behavior:
- If FALSE → hide all payroll enterprise UI + API
- If TRUE → enable routes, UI, and processing

--------------------------------------------------
🧩 BACKEND (Flask)
--------------------------------------------------

Create blueprint:
- payroll_enterprise_bp

Endpoints:

POST /api/payroll/run
GET /api/payroll/history
GET /api/payroll/detail/<id>

Logic:
- Calculate full payroll:
  gross = salary + allowances
  deductions = bpjs + tax + penalties
  net = gross - deductions

All calculations must be modular functions:
- calculate_bpjs()
- calculate_tax_pph21()
- calculate_thr()
- calculate_overtime()

--------------------------------------------------
🖥️ FRONTEND (ADMIN DASHBOARD)
--------------------------------------------------

Create new admin menu:

"Payroll Enterprise"

Pages:
1. Payroll Config
2. Employee Payroll Profile
3. Run Payroll
4. Payroll History
5. Payslip Detail (modal)

UI REQUIREMENTS:
- Follow existing dashboard.css style
- Clean, modern, non-overlapping layout
- Table + card hybrid layout
- Highlight NET SALARY clearly

--------------------------------------------------
📄 PAYSLIP OUTPUT
--------------------------------------------------

Generate structured payslip:

- Employee info
- Salary breakdown:
  + Basic salary
  + Allowances
  - BPJS
  - Tax
  - Other deductions
= NET SALARY

Optional:
- Export JSON (future PDF ready)

--------------------------------------------------
🔐 SECURITY
--------------------------------------------------

- Only ADMIN can run payroll
- Log all payroll runs
- Prevent duplicate run in same period

--------------------------------------------------
🚀 FUTURE READY
--------------------------------------------------

Code must be:
- Extendable for multi-client
- Ready for export (PDF, Excel)
- API-ready for mobile app

--------------------------------------------------

Implement strictly step-by-step. Do not skip layers, do not jump ahead, and do not produce partial or placeholder logic.
Every module must be clean, complete, and properly structured before moving to the next—no rushed or sloppy output will be accepted.