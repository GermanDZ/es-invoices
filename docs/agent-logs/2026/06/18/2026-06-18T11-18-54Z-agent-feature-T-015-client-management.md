# Agent Run Log — T-015

- **Task:** T-015 — Client/contact management (recipient fiscal data)
- **Branch:** feature/T-015-client-management
- **Phase:** construction · **Iteration:** 14 · **Track:** standard (solo)
- **Start:** 2026-06-18T11:11:11Z · **End:** 2026-06-18T11:18:54Z
- **Commits:** 8946afcb5df04a822e859d8e09ff44706b93ad00 (feat), 3eec367 (promote spec)

## Files changed
- New `clients` app: models, validation, forms, services, views, urls, templates, tests, migration 0001
- `invoicing/models.py` + migration 0002 — nullable `Invoice.client` provenance FK
- `config/settings.py`, `config/urls.py` — register app + routes
- `docs/changes/T-015/` — spec, design, completion verification

## Decisions
- New `clients` Django app (modular monolith, arch §4) rather than a sub-module of invoicing.
- Tax-id validation = format + control-char checksum (DNI/NIE/CIF), offline; resolves UC-003 validation-depth open point.
- Type-conditional rule single-homed in `Client.clean`; B2C may omit tax-id (D-2).
- Snapshot stays the legal record; `Invoice.client` FK is additive provenance only.

## Result
Full suite 92 green (2 Postgres-gated skips); fence + check-docs clean. All 6 requirements graded ✅.
