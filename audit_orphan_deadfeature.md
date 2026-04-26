<!-- Static verification report. Do not delete or reconnect files from this note alone. -->
# Audit: Orphan / Dead Feature Candidates

Updated: 2026-04-26

Scope: LOW / IMPROVEMENT item 1 from `audit_gap_anomali_orphan_roadmap_upgrade.md`.

This report is intentionally conservative. Every item below is a candidate or status note only. No file should be deleted, reconnected, or routed based only on this document without a separate runtime check and product decision.

## Verification Method

- Scanned `templates/dashboard/*.html` against `render_template("dashboard/...")` usage in `app.py`.
- Cross-checked dashboard navigation in `templates/dashboard/base.html`.
- Scanned static JS/CSS references from templates.
- Checked helper function definitions versus call sites with exact-name search.
- Checked API endpoints used by reports/payroll templates against `app.py`.

## Action Checklist

Use this checklist to handle findings point by point. Keep every item unchecked until it has been verified in runtime or resolved by a separate code change.

### A. Confirmed Active / Keep

- [ ] Re-test `templates/dashboard/admin_reports.html` in browser and confirm `/api/clients` plus `/api/reports/*` return expected data.
- [ ] Re-test `templates/dashboard/admin_payroll.html` in browser and confirm `/api/employees`, `/api/sites`, and `/api/payroll/*` calls do not throw console/API errors.
- [ ] Re-test `templates/dashboard/admin_qr.html` and confirm QR payload generation works for allowed tier/users.
- [ ] Re-test `templates/dashboard/manual_attendance.html` from `/dashboard/manual_attendance`.
- [ ] Re-test `templates/dashboard/upgrade_prompt.html` from a locked feature path.
- [ ] Keep `_approve_manual_request_atomic(...)` as the active approval path and cover it with manual attendance tests before touching legacy helpers.

### B. Orphan / Dead Feature Candidates

- [ ] `templates/dashboard/admin_shifts.html`: decide whether shift management should be restored, moved into Sites/Settings, or deprecated.
- [ ] `templates/dashboard/admin_shifts.html`: verify staging/production logs for `/dashboard/admin/shifts` or related shift-page usage before any deletion decision.
- [ ] `templates/dashboard/admin_manual_attendance.html`: verify that all admin manual attendance work is covered by `admin_attendance.html`.
- [ ] `templates/dashboard/admin_manual_attendance.html`: if confirmed unused, mark as deprecated in a follow-up commit before any removal.
- [ ] `static/js/dashboard_employee.js`: verify whether a desktop employee dashboard is still planned or fully replaced by `dashboard_employee_mobile.js`.
- [ ] `static/js/dashboard_employee.js`: update docs that still reference it if the mobile implementation is canonical.
- [ ] `_is_enterprise(user)`: review entitlement/tier logic before deciding whether this helper is obsolete.
- [ ] `_approve_manual_request(request_id, reviewer, note)`: keep as legacy helper until manual attendance approval tests exist.
- [ ] `_insert_manual_attendance_record(request_row)`: decide whether to remove it or reuse it as the canonical insert helper after test coverage exists.

### C. Repo Hygiene Follow-up

- [x] Confirm installer binaries and local scratch/debug files are no longer tracked in the next commit.
- [x] Confirm `.dockerignore` excludes DB, uploads, logs, caches, installer binaries, and local diagnostic scripts from Docker build context.
- [x] Move local tooling into ignored `tools/` folders: `tools/local/`, `tools/installers/`, and `tools/backups/`.
- [ ] Decide whether any scratch script should be rewritten into a safe documented script under `scripts/`.

## Rechecked Items From Previous Audit

### Confirmed Active / Keep

- `templates/dashboard/admin_reports.html`
  - Status: active.
  - Evidence: rendered by admin route `GET /dashboard/admin/reports`; linked from dashboard sidebar; uses `/api/clients` and `/api/reports/*`, and those API routes now exist in `app.py`.
  - Note: previous "tanpa route" finding is obsolete.

- `templates/dashboard/admin_payroll.html`
  - Status: active.
  - Evidence: rendered by admin route `GET /dashboard/admin/payroll`; linked from dashboard sidebar; uses `/api/employees`, `/api/sites`, and `/api/payroll/*`.
  - Note: not orphan. Remaining issues are production-readiness / feature behavior, not dead-code status.

- `templates/dashboard/admin_qr.html`
  - Status: active.
  - Evidence: rendered by admin route `GET /dashboard/admin/qr`; linked from dashboard sidebar; `static/js/admin_qr.js` is loaded by the template.

- `templates/dashboard/manual_attendance.html`
  - Status: active.
  - Evidence: rendered by app route `GET/POST /dashboard/manual_attendance`.

- `templates/dashboard/upgrade_prompt.html`
  - Status: active.
  - Evidence: rendered by multiple feature-gating branches for QR, manual attendance, reports, and payroll.

- `_approve_manual_request_atomic(...)`
  - Status: active.
  - Evidence: called by API approval flow and admin manual-attendance approval flow.

### Still Candidate Orphan / Dead Feature

- `templates/dashboard/admin_shifts.html`
  - Status: orphan candidate.
  - Evidence: no `render_template("dashboard/admin_shifts.html")` reference found; no sidebar/menu link found; template posts to `admin.settings_shifts_create`, `admin.settings_shifts_update`, `admin.settings_shifts_toggle`, and `admin.settings_shifts_delete`, but matching routes were not found in `app.py`.
  - Recommendation: mark deprecated until a shift-management decision is made. Do not connect or delete in this pass.

- `templates/dashboard/admin_manual_attendance.html`
  - Status: orphan candidate.
  - Evidence: no render reference found. Current `GET /dashboard/admin/manual_attendance` route redirects into the attendance page anchor instead of rendering this template.
  - Recommendation: mark deprecated after runtime confirmation that all manual attendance admin flow is handled by `admin_attendance.html`.

- `static/js/dashboard_employee.js`
  - Status: stale asset candidate.
  - Evidence: no active template loads `js/dashboard_employee.js`; employee dashboard loads `js/dashboard_employee_mobile.js`. References found only in docs.
  - Recommendation: mark deprecated or update docs if desktop employee dashboard was intentionally replaced by the mobile implementation.

- `_is_enterprise(user)`
  - Status: unused helper candidate.
  - Evidence: definition found, no call site found.
  - Recommendation: keep note as unused helper; remove only after entitlement/tier logic is reviewed.

- `_approve_manual_request(request_id, reviewer, note)`
  - Status: unused helper candidate.
  - Evidence: definition found, approval flows call `_approve_manual_request_atomic(...)` instead.
  - Recommendation: keep note as legacy helper; do not delete until manual attendance test coverage exists.

- `_insert_manual_attendance_record(request_row)`
  - Status: unused helper candidate.
  - Evidence: definition found, no call site found. Atomic approval inserts attendance inline.
  - Recommendation: keep note as legacy helper; decide later whether to fold insertion into one canonical helper.

### Static Assets / Repo Artifacts

- `static/css/employee_mobile.css.bak`
  - Status: tracked backup artifact.
  - Evidence: no template or code reference found.
  - Recommendation: repo hygiene item, not feature wiring. Remove from git tracking or quarantine outside repo history; keep local backup only if still needed.

## Runtime Verification Checklist

- [ ] Log in as `hr_superadmin`.
- [ ] Visit Reports, Payroll, QR, Manual Attendance, Attendance, Settings, and Sites from the dashboard sidebar.
- [ ] Confirm browser console has no 404 for JS/CSS/API calls.
- [ ] Visit `/dashboard/admin/manual_attendance` and confirm redirect behavior is expected.
- [ ] Search production or staging access logs for `admin_shifts.html`, `/dashboard/admin/shifts`, and old employee desktop asset usage before any future deletion.

## Current Recommendation

- Do not delete or reconnect orphan candidates in this pass.
- Treat `admin_shifts.html`, `admin_manual_attendance.html`, `dashboard_employee.js`, `_is_enterprise`, `_approve_manual_request`, and `_insert_manual_attendance_record` as deprecated candidates pending runtime verification.
- Continue LOW / IMPROVEMENT point 2 by cleaning repository hygiene: ignore local binaries/runtime artifacts, add Docker build exclusions, and untrack installer/backup/debug artifacts while preserving local files.
