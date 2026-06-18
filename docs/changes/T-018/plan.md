---
id: T-018
title: Basic invoice status tracking (issued / sent)
status: ready   # proposed → ready → in-progress → done → verified
priority: low   # critical | high | medium | low
estimate: 0.5–1 session
plan: docs/roadmap.md#construction
depends-on: [T-014, T-016]
blocks: []
last-synced: ""
touches:
  - invoicing/models.py
  - invoicing/migrations/
  - documents/services.py
  - invoicing/tests/
  - documents/tests/
---

# T-018 — Basic invoice status tracking (issued / sent)

## Story

> **As an** autónomo issuing invoices through FacturaSimple
> **I want** each invoice to record whether it has merely been issued or also
> sent to its recipient
> **So that** I can tell at a glance which issued invoices still need to be
> delivered, without re-reading my sent-mail folder.

INVEST check:
✅ Independent — builds only on shipped T-016/T-014; no other pending task gates it.
✅ Negotiable — the state set (issued / sent) is fixed by S-6; the encoding is open.
✅ Valuable — closes the "did I send it?" gap, the last S-6 scope item.
✅ Estimable — one nullable field + a save point + a derived property.
✅ Small — single field, one migration, one wiring point.
✅ Testable — each state is an observable property/timestamp.

## Analysis Context

- **Domain.** Invoice lifecycle state on the `Invoice` header
  (`invoicing/models.py:50`). Today the only lifecycle marker is the `issued`
  boolean; "sent" is not persisted anywhere — T-016's `send_invoice_email`
  returns Django's sent-count and logs an instrumentation line but writes
  nothing back to the invoice (T-016 plan.md deferred this to T-018).
- **Scope boundaries.** S-6 is exactly *"issued / sent state per invoice"*
  (`docs/scope.md:34`). This task does **not** surface AEAT submission outcome
  (accepted / rejected / pending) into invoice status — that lives in
  `SubmissionAttempt` (T-014) and stays there. It does not add UI/views, does
  not add a "sent" state to corrective/annulment flows beyond what falls out of
  the shared field, and does not model partial/failed-send retries.
- **Definition of done.** An `Invoice` exposes a three-value derived `status`
  (`draft` / `issued` / `sent`); a successful `send_invoice_email` stamps the
  invoice so its status reads `sent`; querying invoices by state is possible
  from the ORM. The full test suite is green.

> **Assumption:** "sent" is persisted as a nullable `sent_at` timestamp on
> `Invoice` (not a free-standing status enum column); the human-readable
> `status` is *derived* from `issued` + `sent_at`. A timestamp is strictly more
> information than a boolean (when, not just whether) and keeps a single source
> of truth. *(Vetoable at review.)*
> **Assumption:** the stamp is written inside `send_invoice_email` on a
> successful send (the one place the send event is known), and a re-send updates
> `sent_at` to the latest successful delivery rather than preserving the first.
> *(Vetoable at review.)*

## Requirements

1. `Invoice` persists a nullable `sent_at` datetime, defaulting to `None`
   (not-yet-sent), set only when delivery succeeds.
   - **Given** a freshly issued invoice **When** it is loaded from the DB
     **Then** `sent_at is None`.

2. `Invoice` exposes a derived `status` property returning `"draft"` when not
   issued, `"issued"` when issued but `sent_at is None`, and `"sent"` when
   `sent_at` is set.
   - **Given** an invoice with `issued=False` **When** `invoice.status` is read
     **Then** it returns `"draft"`.
   - **Given** an issued invoice with `sent_at=None` **When** `invoice.status`
     is read **Then** it returns `"issued"`.
   - **Given** an issued invoice with `sent_at` set **When** `invoice.status` is
     read **Then** it returns `"sent"`.

3. A successful `send_invoice_email` stamps `sent_at` and persists it; the email
   behaviour (recipient resolution, attachment, return value) is otherwise
   unchanged.
   - **Given** an issued invoice with a resolvable recipient **When**
     `send_invoice_email` returns a non-zero sent count **Then** the reloaded
     invoice has `sent_at` set and `status == "sent"`.

4. A failed/zero send does not stamp the invoice.
   - **Given** an issued invoice whose send returns `0` (or raises before
     sending) **When** the call completes **Then** the reloaded invoice still
     has `sent_at is None`.

5. Stamping `sent_at` does not violate the issued-invoice immutability guard
   (`sent_at` is not an identity field).
   - **Given** an already-issued invoice **When** `send_invoice_email` stamps
     `sent_at` **Then** `save()` succeeds without raising `ValidationError`.

6. Re-sending updates `sent_at` to the later send time.
   - **Given** an invoice already marked sent at T1 **When** it is sent again at
     T2 > T1 **Then** the reloaded `sent_at` equals T2.

## Behavior Delta

**Added** — behavior that did not exist before (no prior Ring-1 artifact models
per-invoice send state):
- An invoice now records *whether and when* it was sent to its recipient
  (`sent_at`) and reports a three-value lifecycle `status`.
- `send_invoice_email` gains a persistence side effect (stamping `sent_at`) on
  successful delivery — previously it was fully read-only.

**Modified** — none. No Ring-1 use case currently asserts a "sent" lifecycle
state; UC-001's postconditions stop at issuance + PDF availability
(`docs/use-cases/UC-001-issue-compliant-invoice.md §postconditions`), and this
task adds the state without changing that flow's existing assertions.

**Removed** — none.

## Entities

- **Invoice** (modified) — `invoicing/models.py:50`; add `sent_at` field +
  `status` property + `mark_sent()` helper.
- **Invoice migration** (new) — `invoicing/migrations/` (adds the `sent_at`
  column).
- **send_invoice_email** (modified) — `documents/services.py:147`; stamp
  `sent_at` on success.
- **SubmissionAttempt** (read-only) — `invoicing` (T-014); AEAT outcome stays
  here, deliberately not folded into invoice status.

## Approach

Encode "sent" as a nullable `sent_at` timestamp on the `Invoice` header rather
than a parallel status column, so there is one fact and the boolean `issued`
+ `sent_at` jointly derive a read-only `status` property — mirroring how T-017's
`corrected_by`/`annulled` are post-issuance overlays absent from
`_IMMUTABLE_WHEN_ISSUED`. A small `mark_sent()` model method centralises the
stamp; `send_invoice_email` calls it only on a confirmed non-zero send so the
delivery point owns the state transition. No new app, no status enum table.

## Structure

**Add:**
- `invoicing/migrations/000X_invoice_sent_at.py` — generated migration.
- Tests for the `status` property and the send-stamps-`sent_at` wiring
  (`invoicing/tests/` for the model, `documents/tests/` for the service path).

**Modify:**
- `invoicing/models.py` — add `sent_at` field, `status` property, `mark_sent()`.
- `documents/services.py` — `send_invoice_email` stamps on success.

**Do not touch:**
- `SubmissionAttempt` / T-014 submission flow — AEAT outcome is not invoice
  status; folding it in is scope creep beyond S-6.
- `_IMMUTABLE_WHEN_ISSUED` — `sent_at` is intentionally mutable post-issue; do
  not add it to the identity guard.
- `documents/services.py` PDF/render path — read-only by design; only the send
  path changes.

## Operations

- [ ] Add `sent_at` (nullable `DateTimeField`) and a derived `status` property
      to `Invoice`, plus a `mark_sent(when=None)` helper that stamps + saves.
- [ ] Generate and commit the migration (`python manage.py makemigrations
      invoicing`); confirm it only adds the column.
- [ ] Wire `send_invoice_email` to call `mark_sent()` after a confirmed non-zero
      send (no stamp on zero/raise).
- [ ] (developer) Add model tests: `status` returns draft/issued/sent across the
      three field combinations; stamping an issued invoice does not trip the
      immutability guard; re-send advances `sent_at`.
- [ ] (developer) Add service test: a successful `send_invoice_email` leaves the
      reloaded invoice `status == "sent"`; a zero-send leaves `sent_at is None`.
- [ ] (tester) Run `python manage.py test invoicing documents` then the full
      suite `python manage.py test`; confirm green and no migration drift.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.).
- `docs/architecture-notebook.md` — module boundaries (compliance/submission
  state stays in its own module; invoice header carries only lifecycle markers).
- Existing test idioms in `documents/tests/test_email.py` (`override_settings`,
  factory helpers, `assertLogs`).

## Safeguards

- **Token / size budget.** ~1 field + ~1 property + ~1 method + 1 migration +
  ~5 tests; if the diff grows a status enum table or touches submission code,
  stop — that is out of scope.
- **Reversibility.** Additive nullable column + a derived read-only property;
  back out by reverting the migration (`migrate invoicing <prev>`) and the two
  edits. No data backfill, no destructive change.
- **No-go zones.** Do not add `sent_at` to `_IMMUTABLE_WHEN_ISSUED`; do not
  change the email body/recipient/return-value contract; do not surface AEAT
  submission outcome into `status`.
- **Concurrency.** `mark_sent()` writes a single non-identity field; use
  `save(update_fields=["sent_at"])` so it cannot race the identity guard or
  clobber unrelated concurrent writes.

## Success Measures

n/a — internal lifecycle field with no user-facing surface or telemetry to read
back in this task (no UI ships in T-018; S-6 is a data-model capability that
later views/status filters build on). Revisit when an invoice-list view exposes
the status filter.

## Rollout

n/a — not user-facing. No UI or API surface ships in T-018; the change is an
additive model field + a persistence side effect on an existing service call,
read-config-free. A feature flag would add no safety over the migration's own
reversibility, so none is used.

## Verification

- `python manage.py test invoicing documents` and `python manage.py test` both
  green.
- `python manage.py makemigrations --check --dry-run` reports no pending model
  changes (migration committed, no drift).
- Manual ORM check: an issued-but-unsent invoice reports `status == "issued"`;
  after `send_invoice_email` succeeds it reports `"sent"`.
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md` — every
  criterion ✅ or a clear gap call-out.
