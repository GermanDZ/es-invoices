---
id: T-017
title: Corrective / cancellation invoices (rectificativa + anulación)
status: done
priority: medium
estimate: 1–2 sessions
plan: docs/roadmap.md#construction
depends-on: [T-013, T-014]
blocks: [T-018]
last-synced: ""
touches:
  - invoicing/
  - compliance/
  - docs/use-cases/UC-004-issue-corrective-invoice.md
  - docs/use-cases/UC-005-annul-invoice-record.md
---

# T-017 — Corrective / cancellation invoices (rectificativa + anulación)

## Story

> **As an** autónomo who has issued an invoice,
> **I want** to legally correct/reverse a valid invoice (factura rectificativa) or
> void a record sent in error (Verifactu anulación),
> **So that** I can fix a mistake and stay Verifactu-compliant without breaking the
> hash-chain or the gap-free numbering of my real sales.

INVEST check:
✅ Independent (builds only on shipped T-012/T-013/T-014) · ✅ Negotiable (subtype
coverage is scoped, not fixed) · ✅ Valuable (closes S-5/D-1, a compliance promise) ·
✅ Estimable (the anulación record path already exists) · ✅ Small (one app surface +
two flows) · ✅ Testable (every flow has an observable pre/postcondition)

## Analysis Context

- **Domain.** The corrective/cancellation surface of S-5 (REQ-004). Two distinct
  legal acts: a **factura rectificativa** (UC-004 — correct/reverse a *valid* sale,
  a new invoice in a dedicated series carrying a Verifactu *alta* of rectificativa
  type) and a **Verifactu anulación** (UC-005 — void a record *sent in error*, no
  new invoice, a *registro de anulación* chained over the original). The annulment
  primitives already ship (`VerifactuRecord.ANULACION`, `generate_anulacion()`,
  `build_registro_anulacion()`, `compute_huella_anulacion()` — all from T-013); the
  rectificativa-type *alta* and the Invoice-side linkage/status do not.
- **Scope boundaries.** Does **not** cover: TicketBAI / foral territories (N-6);
  full invoice status-tracking UI/state machine (that is **T-018** — this task adds
  only the minimal `corrected`/`annulled` linkage the two postconditions require);
  the *por diferencias* method (deferred — see Assumption); UI layout; B2C
  simplified-invoice corrective specifics beyond reusing the existing recipient
  snapshot. Común-territory invoices only.
- **Definition of done.** A user can, from a service-layer call against an issued
  invoice, (a) issue a rectificativa *por sustitución* — numbered next-in-sequence
  in a rectificativa series, referencing the original, recomputing totals, emitting
  a rectificativa-type *alta* record chained + (when enabled) submitted, and marking
  the original `corrected`; and (b) annul an erroneous record — emitting an
  *anulación* chained + submitted, marking the original `annulled` and excluded from
  the active set. Both paths block when their mandatory legal fields are missing and
  do not consume a series number on failure. The compliance unit suite is green.

> **Assumption:** v1 supports rectificativa **por sustitución** only (the UC-004
> default); *por diferencias* (alt-flow 3a) is deferred to a follow-up. *(Vetoable
> at review.)*
> **Assumption:** the rectificativa *alta* uses `TipoFactura=R1` (error fundamentado
> en derecho / the most common case) with `TipoRectificativa=S` (sustitución);
> exposing the full R1–R5 picker is deferred to product-owner test design (UC-004
> self-critique). *(Vetoable at review.)*
> **Assumption:** "full cancellation of a real sale" (UC-004 alt-flow 2a) is realised
> as a por-sustitución rectificativa whose corrected total is zero — not a separate
> code path. *(Vetoable at review.)*
> **Assumption:** the original-invoice linkage/status is modelled as explicit fields
> on `Invoice` (`corrected_by` FK, `annulled` bool) rather than a general status enum
> — the enum belongs to T-018. *(Vetoable at review.)*

## Requirements

1. **Rectificativa issuance.** A rectificativa is a new `Invoice` numbered
   gap-free in a dedicated rectificativa series, carrying a reference to the original
   invoice and recomputed totals (taxable base, IVA, IRPF) over the corrected lines.
   - **Given** a validly issued invoice and a rectificativa series for the owner,
     **When** the service issues a por-sustitución rectificativa with corrected line
     items, **Then** a new issued Invoice exists with `number == series.last_number`
     (post-advance), a non-null reference to the original, and totals recomputed from
     its own lines.
2. **Rectificativa Verifactu record.** Issuing a rectificativa generates a Verifactu
   *alta* record of rectificativa type (`TipoFactura=R1`, `TipoRectificativa=S`) that
   references the rectified invoice and is chained over the issuer's prior huella.
   - **Given** a freshly issued rectificativa, **When** its compliance record is
     generated, **Then** a `VerifactuRecord` (type ALTA) exists with the rectificativa
     `tipo_factura`, the rectified reference populated, and `previous_huella` equal to
     the issuer chain's prior tail.
3. **Original marked corrected.** Once the rectificativa's record is accepted (or, when
   submission is disabled, once generated), the original invoice is linked to its
   rectificativa and marked `corrected`.
   - **Given** an accepted rectificativa record for original O, **When** issuance
     completes, **Then** `O.corrected_by` points at the rectificativa and `O` reports
     `corrected`; **Given** the rectificativa record is rejected by AEAT, **Then**
     `O.corrected_by` is unset and `O` is not marked corrected.
4. **Annulment of an erroneous record.** Annulling an issued invoice generates a
   Verifactu *registro de anulación* (reusing `generate_anulacion()`), submits it via
   the AD-3 gateway, and on acceptance marks the original `annulled` and excluded from
   the active set; no new Invoice and no series number is consumed.
   - **Given** an issued invoice with an accepted *alta* record, **When** the service
     annuls it, **Then** a `VerifactuRecord` (type ANULACION) referencing the original
     is persisted and chained, `invoice.annulled` is true, and no new Invoice row was
     created.
5. **Annulment guardrail.** The annulment path is reserved for erroneous records; the
   service refuses to annul once a rectificativa exists for the invoice (a real-sale
   correction), steering callers to the rectificativa path (UC-005 exception 2b).
   - **Given** an invoice already linked via `corrected_by`, **When** annulment is
     attempted, **Then** the service raises a domain error and persists no anulación
     record.
6. **Mandatory-field validation, no number burn.** Both flows validate mandatory legal
   fields (rectificativa: original reference + rectificativa type; anulación: a
   submitted original record) and abort without consuming a series number or leaving a
   partial record on failure.
   - **Given** a rectificativa issuance missing the original reference, **When** issuance
     runs, **Then** it raises before assigning a number and `series.last_number` is
     unchanged.

## Behavior Delta

**Added** — behavior that did not exist before:
- Issue a factura rectificativa (por sustitución) — `docs/use-cases/UC-004-issue-corrective-invoice.md` (promote `draft → approved`).
- Annul a Verifactu record sent in error — `docs/use-cases/UC-005-annul-invoice-record.md` (promote `draft → approved`).
- Rectificativa-type *alta* metadata (`TipoFactura=R1`, `TipoRectificativa=S`, rectified reference) on the compliance record path.

**Modified** — behavior that changes; cite the Ring-1 artifact + section:
- Invoice lifecycle gains terminal `corrected` / `annulled` outcomes after issuance —
  `docs/use-cases/UC-001-issue-compliant-invoice.md §postconditions` (an issued invoice
  was previously terminal; it can now be superseded or voided).

**Removed** — none.
- n/a

## Entities

- **Invoice** (modified) — `invoicing/models.py:50` — add `corrected_by` (self-FK,
  nullable) and `annulled` (bool); read existing immutability rules.
- **Series** (read-only / reused) — `invoicing/models.py:27` — a rectificativa series is
  just a `Series` with its own `prefix`; gap-free guarantee reused, not changed.
- **VerifactuRecord** (modified) — `compliance/models.py:42` — rectificativa is an ALTA
  record needing rectificativa-type fields + rectified reference; ANULACION type already
  exists.
- **generate_alta / build_registro_alta** (modified) — `compliance/services.py:60`,
  `compliance/records.py:129` — accept optional rectificativa metadata.
- **generate_anulacion** (read-only / reused) — `compliance/services.py:117` — called as-is.
- **submit_record** (read-only / reused) — `submission/services.py:39` — AD-3 boundary, unchanged.

## Approach

Layer the two flows as **service-layer orchestrators** in the `invoicing`/`compliance`
apps, reusing the shipped chain/submission machinery rather than re-implementing it. The
annulación path is almost entirely composition (`generate_anulacion()` → `submit_record()`
→ mark `annulled`), so its work is the Invoice-side guardrail + status. The rectificativa
path is a thin specialisation of issuance: clone-from-original into a rectificativa series,
recompute via the existing totals calc, then call `generate_alta()` extended to carry
rectificativa metadata (`TipoFactura`, `TipoRectificativa`, rectified `IDFactura`
reference) into `build_registro_alta()`'s XML. Keep all Verifactu rule changes behind the
compliance module interface (AD-2). Original-vs-rectificativa linkage and the
`corrected`/`annulled` flags live on `Invoice` as minimal explicit fields — not a status
enum (that is T-018).

## Structure

**Add:**
- `invoicing/migrations/00NN_invoice_corrective_fields.py` — `Invoice.corrected_by`, `Invoice.annulled`.
- `compliance/tests/test_rectificativa.py` — rectificativa alta record (R1/S), reference, chaining.
- `invoicing/tests/test_corrective.py` — rectificativa issuance, original marked corrected, annulment guardrail, no-number-burn.

**Modify:**
- `invoicing/models.py` — add `corrected_by` (self-FK), `annulled` (bool) to `Invoice`.
- `invoicing/services.py` — add `issue_rectificativa(original, *, series, corrected_items, …)` and `annul_invoice(invoice, …)` orchestrators (reuse `issue_invoice` numbering + `select_for_update`).
- `compliance/records.py` — `build_registro_alta()` accepts optional rectificativa params (tipo_factura, tipo_rectificativa, rectified ref); emit the corresponding XML block.
- `compliance/services.py` — `generate_alta()` threads rectificativa metadata through to the builder.

**Do not touch:**
- `submission/` — the AD-3 gateway/outcome contract is reused as-is; no adapter change.
- `compliance/services.py::generate_anulacion` — already correct; call it, don't fork it.
- Full invoice status enum / issued→sent tracking — owned by **T-018**; add only the two fields the postconditions require.

## Operations

- [x] Add `Invoice.corrected_by` (nullable self-FK) and `Invoice.annulled` (bool) + migration; confirm they are excluded from the issued-immutability set (post-issue mutation must be allowed).
- [x] Implement `annul_invoice()` in `invoicing/services.py`: guardrail (refuse if `corrected_by` set), call `generate_anulacion()` + `submit_record()`, mark `annulled` on acceptance/disabled — transactional, no new Invoice.
- [x] Extend `compliance` (`build_registro_alta` + `generate_alta`) to carry rectificativa metadata (`TipoFactura=R1`, `TipoRectificativa=S`, rectified reference) into the alta XML.
- [x] Implement `issue_rectificativa()` in `invoicing/services.py`: clone-from-original into a rectificativa series, recompute totals, number gap-free, generate rectificativa alta + submit, mark original `corrected` on acceptance.
- [x] (tester) Write `compliance/tests/test_rectificativa.py` and `invoicing/tests/test_corrective.py` covering all six requirements' scenarios incl. mandatory-field/no-number-burn and the annulment guardrail; run `.venv/bin/python -m django test invoicing compliance`.
- [x] (analyst) Promote `UC-004` and `UC-005` `draft → approved` via `/openup-create-use-case` (re-run through the rubric), reflecting the v1 por-sustitución / R1 scope assumptions.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs/conventions.md` (if exists) — project conventions
- `docs/architecture-notebook.md` — AD-2 (versioned compliance module), AD-3 (submission interface), AD-6/Q-1 (transactional gap-free numbering)

## Safeguards

- **Token / size budget.** Reuse shipped primitives; net new logic should be two
  service orchestrators + two `Invoice` fields + rectificativa XML params — not a new app.
- **Reversibility.** New behavior is additive (new fields default null/false, new service
  verbs); the migration is forward-only-safe. Rectificativa series are independent of the
  main series, so a backout leaves real-sale numbering intact.
- **No-go zones.** Must NOT mutate an issued original's immutable identity fields
  (`series_id`, `number`, `issue_date` — `invoicing/models.py` immutability set); must NOT
  break the issuer huella chain (every new record chains over the prior tail under the
  `IssuerChain` row-lock); must NOT consume a series number on a failed/blocked issuance.
- **Compliance invariant.** Annulment never deletes — it marks `annulled` and chains a
  *registro de anulación* (UC-005 scope). All Verifactu field/order rules stay behind the
  compliance module interface (AD-2).

## Rollout

**Flagged?** No new flag. Both flows reach AEAT through the **existing**
`AEAT_SUBMISSION_ENABLED` kill-switch (`config/settings.py`, T-014): when off,
`submit_record()` returns `DISABLED` and records are generated/chained but not sent — the
same safety the alta path already has. A separate corrective flag would add no safety the
existing switch doesn't already provide. The new service verbs are not wired to any UI in
this task, so there is no user-facing surface to gate independently. No flag-removal
follow-up is created (none added).

## Success Measures

We expect **first-submission acceptance of rectificativa + anulación records** (Q-2's
≥99% target, extended to corrective records) to hold at **≥99%** within **the first 30
days** of the corrective flows being exercised against AEAT. Instrumentation: the
`SubmissionAttempt` rows for records whose `record_type=ANULACION` or whose `tipo_factura`
is a rectificativa subtype — read `status=ACCEPTED` over total verdicts. Read-back: 30
days after the first production corrective submission. *(Pre-UI this is exercised via the
preproducción sandbox in the test suite; the production read-back lands with the UI task.)*

## Verification

- `.venv/bin/python -m django test invoicing compliance` is green, including the new
  `test_rectificativa.py` and `test_corrective.py`.
- A rectificativa issuance against a fixture issued invoice produces a new Invoice in a
  rectificativa series, an ALTA `VerifactuRecord` with `tipo_factura=R1` referencing the
  original, and sets `original.corrected_by`.
- An annulment produces an ANULACION `VerifactuRecord` chained over the prior tail, sets
  `invoice.annulled`, creates no new Invoice, and is refused when `corrected_by` is set.
- Mandatory-field omission aborts without advancing `series.last_number`.
- UC-004 and UC-005 are `approved`.
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md` — every criterion
  ✅ or a clear gap call-out.
