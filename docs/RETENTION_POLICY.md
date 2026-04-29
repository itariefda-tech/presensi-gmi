# Retention Policy

Retention defaults are stored in `retention_policies`.

| Data Type | Retention | Action |
| --- | ---: | --- |
| attendance | 1825 days | ARCHIVE |
| payroll | 1825 days | ARCHIVE |
| patrol_reports | 1095 days | ARCHIVE |
| audit_logs | 1825 days | ARCHIVE |
| temporary_uploads | 90 days | DELETE |
| password_reset_tokens | 30 days | DELETE |

## Policy Rules

- Archive business-critical data before deletion.
- Delete temporary uploads after the active retention window.
- Keep audit records long enough for enterprise review and dispute handling.
- Soft-deleted records remain hidden from default UI but are retained until policy cleanup.

## Future Job

Add a scheduled retention worker that reads `retention_policies`, archives eligible records, and records the cleanup in `audit_logs`.
