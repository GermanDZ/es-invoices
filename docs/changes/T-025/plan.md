---
id: T-025
title: Close UC-004/UC-005 behaviour gaps (por-diferencias, rectificativa PDF marking, annul-while-pending, active-set exclusion, recipient email)
status: ready
priority: medium
estimate: 1–2 sessions
plan: docs/roadmap.md#construction
depends-on: [T-017]
blocks: []
last-synced: ""
touches:
  - invoicing/services.py
  - invoicing/models.py
  - invoicing/views.py
  - invoicing/forms.py
  - invoicing/migrations/
  - invoicing/tests/
  - documents/services.py
  - documents/templates/documents/invoice.html
  - documents/tests/
  - clients/models.py
  - clients/forms.py
  - clients/services.py
  - clients/migrations/
  - clients/tests/
  - docs/changes/T-025/
---

# T-025 — Close UC-004/UC-005 behaviour gaps

## Story

> **As an** autónomo using FacturaSimple
> **I want** corrective and annulment flows to behave exactly as the approved
> use cases promise (a *por diferencias* correction, a clearly-marked
> rectificativa PDF, an annulment that respects a still-pending record, annulled
> invoices dropping out of the active set, and emails reaching my client's saved
> address)
> **So that** the legally-required correction workflows are conformant and a
> non-accountant can trust them end to end.

INVEST check:
✅ Independent — no unfinished dependency (T-017 done) · ✅ Negotiable — each gap
is a separate requirement · ✅ Valuable — closes acceptance criteria of *approved*
use cases · ✅ Estimable — five bounded gaps in known files · ✅ Small — 1–2
sessions, no new architecture · ✅ Testable — every requirement carries a failable
scenario below.

## Analysis Context

- **Domain.** The corrective/cancellation slice (S-5, REQ-004) — `invoicing`
  (rectificativa + annul engine and UI), `compliance` (Verifactu record builder,
  already supports both rectificativa methods), `documents` (PDF + email), and
  `clients` (recipient fiscal data).
- **Why the spec exists.** UC-004 and UC-005 are **approved** (`status: approved`)
  but a coverage review found the implementation does not yet meet five of their
  acceptance criteria. This is pure **spec-conformance debt** — fix the code to
  the approved use cases; the use cases themselves are correct and are **not**
  edited.
- **Scope boundaries.** Does NOT build an invoice **list/dashboard UI** (none
  exists yet — out of scope, a future task); does NOT change numbering, the
  hash-chain, signing, or the AEAT adapter; does NOT touch TicketBAI/foral (N-6).
  The active-set requirement is met by delivering the canonical selector + test,
  not a listing screen.
- **Definition of done.** All five requirements below are green in CI, the
  rubric is all-✅, and `python3 manage.py test` (in `.venv`) passes including the
  new tests.

> **Assumption:** *Por diferencias* in v1 reuses the same line-item form as *por
> sustitución*; the método selector only switches `TipoRectificativa` ("S"→"I")
> and (for "I") omits the `ImporteRectificacion` block — the user still enters the
> corrected/delta lines by hand. No separate delta-only UI is built. *(Vetoable at review.)*
> **Assumption:** "Cancel the pending submission" (UC-005 2a) means: mark the
> invoice annulled **locally**, generate **no** anulación record, and stamp the
> latest pending `SubmissionAttempt` as cancelled — submission is synchronous
> today, so there is no external queue to dequeue. *(Vetoable at review.)*
> **Assumption:** The active set is delivered as an `Invoice` queryset method
> `active()` (excludes `annulled=True`); direct detail/pdf/rectificar/annul access
> to an annulled invoice stays reachable (exclusion is from *listings*, not record
> access). *(Vetoable at review.)*
> **Assumption:** `Client.email` is an **optional** `EmailField` for both B2B and
> B2C (validated when present); it does not become a required field. *(Vetoable at review.)*

## Requirements

1. **Por-diferencias method is reachable.** `issue_rectificativa` accepts the
   rectificativa method (default *sustitución*) and the UI exposes it, so the
   value flows to `compliance.generate_alta`'s `tipo_rectificativa`.
   - **Given** an issued invoice on the rectificativa form **When** the user
     selects *por diferencias* and confirms **Then** the generated rectificativa
     alta record carries `TipoRectificativa="I"` and emits no `ImporteRectificacion`.
   - **Given** the default (no method change) **When** the user confirms **Then**
     the record carries `TipoRectificativa="S"` (today's behaviour, unchanged).

2. **Rectificativa PDF is clearly marked and cites the corrected invoice.** The
   rendered PDF of a rectificativa is labelled as such and shows the corrected
   invoice's NumSerie (UC-004 postcondition).
   - **Given** a rectificativa invoice (its `corrects` set is non-empty) **When**
     its PDF is rendered **Then** the document shows a *FACTURA RECTIFICATIVA*
     marking and the corrected invoice's NumSerie.
   - **Given** an ordinary (non-corrective) invoice **When** its PDF is rendered
     **Then** no rectificativa marking or reference appears.

3. **Annul-while-pending cancels the pending submission instead of sending an
   anulación.** UC-005 alt-flow 2a.
   - **Given** an issued invoice whose alta record's latest submission is
     `pending` (not accepted) **When** the user annuls it **Then** no anulación
     record is generated, the pending `SubmissionAttempt` is marked cancelled, and
     the invoice is marked `annulled` locally.
   - **Given** an issued invoice whose alta was accepted (or submission disabled)
     **When** the user annuls it **Then** an anulación record is generated and
     submitted (today's behaviour, unchanged).

4. **Annulled invoices are excluded from the active set.** UC-005 postcondition.
   - **Given** one annulled and one non-annulled invoice for an owner **When**
     `Invoice.objects.active()` is queried **Then** only the non-annulled invoice
     is returned.
   - **Given** an annulled invoice **When** its detail page is requested directly
     **Then** it is still reachable (exclusion is from listings, not record access).

5. **Recipient email resolves from a saved client.** `Client` carries an optional
   `email`, and `send_invoice_email` uses it when `to_email` is omitted.
   - **Given** a client with a saved email and an invoice carrying that client FK
     **When** `send_invoice_email` is called with no `to_email` **Then** the email
     is sent to the client's saved address.
   - **Given** the client form **When** saving with an invalid email **Then** the
     form is rejected with a field error; **When** saving with a valid (or empty)
     email **Then** it persists.

## Behavior Delta

**Added** — behavior that did not exist before:
- `Client.email` field; `documents.services._recipient_email` (already
  forward-compatible via `getattr`) now resolves a real address — auto-email to a
  saved client becomes functional.

**Modified** — behavior that changes; Ring-1 artifact + section cited:
- Rectificativa method is user-selectable; *por diferencias* becomes reachable —
  `docs/use-cases/UC-004-issue-corrective-invoice.md §alt-flow-3a`.
- Rectificativa PDF is marked and cites the corrected invoice —
  `docs/use-cases/UC-004-issue-corrective-invoice.md §postconditions`.
- Annul-while-pending cancels the pending submission rather than sending an
  anulación — `docs/use-cases/UC-005-annul-invoice-record.md §alt-flow-2a`.
- Annulled invoices drop out of the active set —
  `docs/use-cases/UC-005-annul-invoice-record.md §postconditions`.

**Removed** — none.

## Entities

- **Invoice** (modified) — `invoicing/models.py`: add `objects.active()` queryset
  excluding `annulled`; `corrects` reverse manager already links rectificativa→original.
- **issue_rectificativa** (modified) — `invoicing/services.py`: add method param.
- **annul_invoice** (modified) — `invoicing/services.py`: pending-aware branch.
- **SubmissionAttempt** (read + lightweight write) — `submission/models.py`:
  read latest status; mark a pending one cancelled.
- **Client** (modified) — `clients/models.py`: add `email` field.
- **invoice.html** (modified) — `documents/templates/documents/invoice.html`:
  rectificativa marking.

## Approach

Each gap is a localized, additive change behind the seams that already exist:
the compliance record builder already accepts `tipo_rectificativa="I"`, so R1 is
only plumbing a selector through the form → service → `generate_alta`. R2 is a
read-only template/context addition in the documents module (which must not write
to the invoice). R3 reads the latest `SubmissionAttempt` status inside
`annul_invoice` and forks before generating an anulación. R4 is a queryset method
plus a test (no consumer screen exists yet). R5 is a model field + migration +
form field; the email-resolution code is already forward-compatible. Keep every
rule behind its module — no cross-module reach-through.

## Structure

**Add:**
- `invoicing/migrations/0004_*.py` — (auto) any field/queryset change needing one
- `clients/migrations/0002_client_email.py` — (auto) `Client.email`

**Modify:**
- `invoicing/services.py` — `issue_rectificativa(method=...)`; pending-aware
  `annul_invoice`.
- `invoicing/models.py` — `Invoice.objects.active()` (custom manager/queryset).
- `invoicing/forms.py` — método selector on `RectificativaForm`.
- `invoicing/views.py` — pass método from `RectificativaForm` through `_rectify_from_forms`.
- `documents/services.py` — supply rectificativa marking + corrected NumSerie to
  the template context (read-only).
- `documents/templates/documents/invoice.html` — render the marking when present.
- `clients/models.py` — add `email = EmailField(blank=True)`.
- `clients/forms.py` — add `email` to `ClientForm.fields`.
- `clients/services.py` — (only if the snapshot needs to carry email; otherwise
  resolution stays via the client FK in `documents.services`).
- `invoicing/tests/`, `documents/tests/`, `clients/tests/` — one test per requirement.

**Do not touch:**
- `compliance/records.py` / `compliance/services.py` — already support both
  rectificativa methods; R1 only passes the value through.
- `submission/services.py` numbering/retry policy and `AEAT_SUBMISSION_LIVE`
  kill-switch — unchanged.
- Numbering authority (`issue_invoice`) and the hash-chain/signing — out of scope.

## Operations

- [ ] Add `Client.email` (optional `EmailField`) + `email` to `ClientForm.fields`; run `makemigrations clients` and `migrate` using the **`.venv`** python (see Safeguards); add a clients test for valid/invalid/empty email (R5 form half).
- [ ] Thread the rectificativa **método** ("S"/"I") through `RectificativaForm` → `_rectify_from_forms` → `issue_rectificativa(method=...)` → `generate_alta(tipo_rectificativa=...)`, defaulting to "S"; add an invoicing test asserting both `TipoRectificativa` values on the generated record (R1).
- [ ] Make `annul_invoice` pending-aware: when the original alta's latest `SubmissionAttempt` is `pending` (not accepted), mark that attempt cancelled, mark the invoice `annulled` locally, and generate **no** anulación; keep the accepted/disabled path generating an anulación; add invoicing tests for both branches (R3).
- [ ] Add `Invoice.objects.active()` excluding `annulled=True`; add a test that it returns only the non-annulled invoice and that an annulled invoice's detail page still loads (R4).
- [ ] Mark the rectificativa PDF: pass an `is_rectificativa` flag + corrected NumSerie from `render_invoice_pdf` (read-only) and render a *FACTURA RECTIFICATIVA* + corrected-invoice reference in `invoice.html`; add a documents test asserting the marking appears for a rectificativa and is absent for an ordinary invoice, and that `send_invoice_email` resolves the client email when `to_email` is omitted (R2 + R5 resolution half).
- [ ] (tester) Run the full suite in `.venv` (`python manage.py test`), confirm all five requirements green, and record results in `docs/changes/T-025/test-notes.md`.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, process conventions.
- `docs/conventions.md` (if present) — project conventions.
- `docs/architecture-notebook.md` — module boundaries (compliance versioned
  module AD-2; documents is a read-only consumer of invoicing).
- `.venv` dependency rule — see memory `venv-vs-asdf-shim-deps`: `manage.py` uses
  `.venv`; run migrations/tests through it, not the asdf python3 shim.

## Safeguards

- **Module boundary.** `documents` stays a read-only consumer — the PDF/marking
  path must not write to any invoice, line item, series, or compliance record.
- **Numbering invariant.** No change to `issue_invoice` or the gap-free guarantee;
  a failed rectificativa still consumes no number (existing rollback).
- **Compliance module.** Do not re-implement rectificativa record logic in
  `invoicing` — only pass `tipo_rectificativa` through to `compliance.generate_alta`.
- **Kill-switch unchanged.** `AEAT_SUBMISSION_LIVE` still gates every live call;
  the annul-while-pending branch sends nothing to AEAT by construction.
- **Migrations into `.venv`.** Generate and apply migrations with the `.venv`
  interpreter; new deps (none expected) would go in `.venv`, not the shim.
- **Reversibility.** All changes are additive (new field, new queryset method, new
  param with a back-compatible default, template additions); revert = drop the
  migration + revert the diff. No data migration of existing rows beyond the
  nullable/blank `email` default.

## Rollout

**Flagged?** No. These are conformance corrections to already-shipped UC-004/UC-005
flows during Construction (pre-launch, no live users); a feature flag adds no
safety and there is no gradual-rollout need. The only AEAT-facing path
(annul-while-pending) sends *less* to AEAT, and the existing
`AEAT_SUBMISSION_LIVE` kill-switch already gates all live submission — no new
toggle is warranted. `n/a — no new flag; existing kill-switch unchanged.`

## Success Measures

`n/a — pre-launch spec-conformance debt.` There are no live users in the
Construction phase, so no product metric can be read back; the value is closing
acceptance criteria of *approved* use cases. Verified instead by the five
requirement scenarios above, each backed by a new CI test (see §Verification).

## Verification

- `python manage.py test` (run via `.venv`) passes, including the new tests for
  R1–R5; the run is recorded in `docs/changes/T-025/test-notes.md`.
- R1: a test asserts the generated rectificativa record carries `TipoRectificativa="I"`
  for *por diferencias* and `"S"` by default.
- R2: a documents test asserts the rectificativa marking + corrected NumSerie
  appears in the rendered HTML and is absent for an ordinary invoice.
- R3: tests assert no anulación record + cancelled pending attempt when pending,
  and an anulación record when accepted/disabled.
- R4: a test asserts `Invoice.objects.active()` excludes the annulled invoice and
  its detail page still loads.
- R5: tests assert `Client.email` validation and that `send_invoice_email`
  resolves the saved client email when `to_email` is omitted.
- Grade the final spec against `.claude/rubrics/task-spec-rubric.md` — every
  criterion ✅.
