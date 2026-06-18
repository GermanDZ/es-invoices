# T-015 — In-flight design decisions

- **New `clients` Django app** (not a module inside `invoicing`) — mirrors the
  per-subsystem app layout (`certificates`, `compliance`, `invoicing`,
  `submission`) and architecture-notebook §4's distinct "Client management"
  module. AD-1 modular monolith.
- **Tax-id validation = format + control-char checksum** for DNI / NIE / CIF
  (`clients/validation.py`), deterministic and offline — no live AEAT lookup.
  Resolves the UC-003 self-critique "validation depth" open point. DNI/NIE share
  the mod-23 control-letter table; CIF uses the org-letter / digit-sum algorithm
  with per-org-type letter-vs-digit control rules. Known-good anchors in tests:
  `12345678Z` (DNI), `X1234567L` (NIE), `A58818501` (CIF).
- **Type-conditional rule lives in `Client.clean`** (single home), surfaced on
  the `tax_id` field; `ClientForm` is a thin `ModelForm` so the rule flows through
  `full_clean` automatically — no duplication between form and model. B2B requires
  a valid id; B2C may omit it (D-2 simplified-invoice rule) but validates a
  non-empty one.
- **Owner scoping is structural** — every view filters `owner=request.user` via
  `get_object_or_404`, so cross-owner access is a 404 (not a 403 leak).
- **Snapshot, not displacement** — `clients.services.recipient_snapshot` re-runs
  `full_clean` then returns the invoice recipient fields, so a B2B client with a
  bad/missing NIF cannot yield a usable snapshot (req. 5). The new
  `Invoice.client` FK is nullable/additive provenance only — never read by
  numbering or the compliance module (safeguards / no-go zones honored).
- **Test env note:** the worktree has no own venv; ran against the main clone's
  `.venv` (Django 5.2). Full suite 92 green, 2 Postgres-gated skips.

## Completion verification (step 1a/1b)

Graded against `git diff main...HEAD` + green tests:

- R1 ✅ `clients/models.py:Client` (owner FK + fiscal fields) — `test_create_b2b_with_valid_taxid`, `test_list_shows_only_own_clients`
- R2 ✅ `Client.clean` + `clients/validation.py` — `test_create_b2b_invalid_taxid_rejected`, `test_create_b2b_missing_taxid_rejected`
- R3 ✅ B2C optional/validated — `test_create_b2c_without_taxid_ok`, `test_create_b2c_invalid_taxid_rejected`
- R4 ✅ `get_object_or_404(..., owner=request.user)` — `test_cannot_open_another_users_client_edit`, `test_cannot_delete_another_users_client`
- R5 ✅ `clients/services.recipient_snapshot` — `clients/tests/test_services.py` (3)
- R6 ✅ `@login_required` views — `test_anonymous_redirected_to_login`

Success-measure instrumentation ✅ — `Invoice.client` FK + migration `invoicing/0002` committed; the read-back query (non-null rate among issuers with ≥1 client) reads that column. Read-back: 30 days after the clients feature reaches beta.

Full suite: 92 passed, 2 Postgres-gated skips. Rollout: `n/a — no flag` (additive, auth-gated) → no flag-removal row.
