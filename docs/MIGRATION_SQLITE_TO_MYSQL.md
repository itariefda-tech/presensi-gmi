# Migration SQLite To MySQL

## Current State

The app still uses SQLite through `_db_connect()` and `DB_PATH`. Phase 16 keeps all new schema additive and uses ISO date strings to reduce future migration risk.

## Migration Steps

1. Freeze writes and take a SQLite backup.
2. Export schema and data from SQLite.
3. Create MySQL schema with equivalent tables.
4. Convert SQLite-specific constructs:
   - `INTEGER PRIMARY KEY AUTOINCREMENT` to MySQL `BIGINT AUTO_INCREMENT PRIMARY KEY`
   - `TEXT` to `TEXT` or `VARCHAR` where bounded
   - partial indexes to generated constraints or application validation
   - `ON CONFLICT` upsert to `ON DUPLICATE KEY UPDATE`
5. Load reference tables first: `clients`, `sites`, `users`, `employees`.
6. Load transactional tables: `attendance`, `leave_requests`, `payroll`, patrol tables.
7. Load enterprise tables: `client_packages`, `client_addons`, `client_contracts`, `billing_configs`.
8. Load audit and retention tables.
9. Run count checks per table.
10. Run smoke tests for login, attendance, leave, payroll, client profile, and subscription.

## Adapter Readiness

Before switching engine, isolate SQL dialect differences behind a small adapter for:

- connection creation
- upsert syntax
- index creation
- date functions
- pagination

## Data Format Rules

- Dates stay as ISO strings: `YYYY-MM-DD`.
- Date-times stay as `YYYY-MM-DD HH:MM:SS`.
- JSON payloads stay ASCII JSON text.
