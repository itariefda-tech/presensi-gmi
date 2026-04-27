# TODO Phase 16-19 AI Analysis

- [x] Fix syntax bug `ifforbidden` -> `if forbidden` in AI analysis case status endpoint.
- [x] Phase 16 API: add missing endpoints
  - [x] POST `/api/admin/ai-analysis/recalculate`
  - [x] GET `/api/admin/ai-analysis/employee/<id_or_email>`
  - [x] GET `/api/admin/ai-analysis/department/<id>`
  - [x] GET `/api/admin/ai-analysis/client/<id>`
  - [x] GET `/api/admin/ai-analysis/location/<id>`
  - [x] POST `/api/admin/ai-analysis/alerts/<id>/review`
- [x] Phase 17 DB: align AI alerts schema columns with roadmap (safe migration via `_ensure_column`).
- [x] Phase 18 UI: update `templates/dashboard/admin_ai_analysis.html`
  - [x] consume employee drilldown data and keep endpoint available for direct API use
  - [x] add review action for persisted snapshot alert list
- [x] Phase 19 foundation: include predictive preview/disclaimer payload (non-ML placeholder, backward-compatible).
- [x] Run syntax check (`python -m py_compile app.py`).
