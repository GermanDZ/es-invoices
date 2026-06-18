---
id: T-012
title: "Invoicing core: line items, IVA/IRPF, gap-free numbering"
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 2 sessions
plan: docs/roadmap.md#construction   # link to originating plan, if any
depends-on: [T-006]
blocks: [T-013, T-015, T-016]
touches: [invoicing, config]
last-synced: ""    # full git SHA of last code↔spec sync (set by /openup-sync-spec)
---

# T-012 — Invoicing core: line items, IVA/IRPF, gap-free numbering

## Story

> **As an** autónomo issuing invoices in FacturaSimple
> **I want** to build an invoice from line items and have the system compute IVA/IRPF
> and assign the next gap-free number in my series when I issue it
> **So that** every invoice I issue is arithmetically correct and carries an unbroken
> legal sequence the AEAT will accept

INVEST check:
✅ Independent — depends only on T-006 (architecture); builds on the T-011 skeleton ·
✅ Negotiable — rate handling, rounding, and recipient-snapshot model are vetoable
assumptions · ✅ Valuable — the core every other Construction task (T-013/14/15/16)
sits on · ✅ Estimable — 2 sessions · ✅ Small — one `invoicing` app: models + calc +
transactional numbering · ✅ Testable — totals, rate grouping, rounding, and gap-free
numbering (incl. concurrent + rollback) are all assertable

## Analysis Context

State the *why* the spec needs but the code can't show:
- **Domain.** The invoicing core (architecture-notebook §4 "Invoicing core", S-2,
  UC-001 basic flow steps 2–6). It owns the invoice/line-item data model, the
  taxable-base + IVA + IRPF calculation, and **gap-free sequential numbering per series
  under a transactional boundary** (AD-6, Q-1). This is the R-02 surface — the CI test
  suite here is the mitigation.
- **Scope boundaries.** Does NOT generate Verifactu records, hash-chain, or sign — that
  is the versioned compliance module (T-013, AD-2). Does NOT submit to AEAT (T-014). Does
  NOT build the PDF or the email send (T-016). Does NOT build client/contact CRUD (T-015)
  — the recipient's fiscal data is captured as an inline snapshot on the invoice. Does NOT
  build the issue/review **UI** — issuance is exercised as a service-layer action plus
  tests; the screen is a later doc/UI task. Does NOT do *Verifactu-specific* legal-field
  validation (AD-2/T-013); it validates only the structural completeness an invoice needs
  to be issued at all.
- **Definition of done.** A user with a numbering series can assemble an invoice with ≥1
  line item; the system computes per-line amounts, groups the taxable base by IVA rate,
  applies IRPF retention at the invoice level, and rounds to cents deterministically; on
  *issue* the system assigns the next sequential number in that series **atomically** and
  persists the invoice; concurrent issuance never produces a gap or a duplicate; a
  validation failure during issue does **not** consume a number (UC-001 6a); the whole
  calculation + numbering path is covered by a CI test suite that is green.

> **Assumption:** A minimal issuer fiscal identity + numbering **Series** are introduced
> here (the Account & Auth module that owns them per architecture-notebook §4 is not yet
> built), modeled one-business-per-user with ≥1 series (scope.md D-3). *(Vetoable — the
> alternative is to block T-012 on an Account-module task.)*
> **Assumption:** The recipient is stored as a **denormalized fiscal snapshot** on the
> invoice (name, NIF/CIF, address), not a FK to a Client; client management and linking is
> T-015 (UC-003). *(Vetoable at review.)*
> **Assumption:** IVA is a **per-line rate** chosen from the Spanish rates (21 / 10 / 4 / 0
> exempt); IRPF is a single **invoice-level retention percentage** (e.g. 15 or 7), applied
> to the taxable base, defaulting to none/0 unless configured. *(Vetoable at review.)*
> **Assumption:** Rounding follows the standard Spanish rule — amounts are summed and
> rounded to **2 decimals per IVA-rate group** (`ROUND_HALF_UP`), using `Decimal`, never
> float. *(Vetoable at review.)*
> **Assumption:** "Issue" is a **service-layer action** (no UI in this task); UC-001 steps
> 1/5 (UI selection + on-screen review) are exercised through the service + tests, with the
> screen deferred. *(Vetoable at review.)*

## Requirements

1. An invoice can hold one or more line items (description, quantity, unit price, IVA rate),
   and the system computes each line's amount and the invoice's taxable base, IVA total,
   IRPF retention, and grand total using `Decimal` with 2-decimal rounding per IVA-rate
   group.
   - **Given** an invoice with two line items at 21% IVA and one at 10% **When** the totals
     are computed **Then** the taxable base, the IVA total (summed per-rate-group then
     rounded), and the grand total match the expected `Decimal` values to the cent.

2. IVA is applied per line at the line's rate; the taxable base is grouped by rate and each
   group's IVA is rounded independently before summing (no float arithmetic anywhere in the
   calculation path).
   - **Given** line items spanning the 21%, 10%, and 0%-exempt rates **When** totals are
     computed **Then** each rate group reports its own base and IVA, the exempt group adds
     0 IVA, and the invoice IVA total equals the sum of the rounded per-group IVAs.

3. IRPF retention, when configured, is applied as an invoice-level percentage of the
   taxable base and subtracted from the grand total; when not applicable it is omitted
   (UC-001 alt-flow 3a).
   - **Given** an invoice with a 15% IRPF retention configured **When** totals are computed
     **Then** the retention equals 15% of the taxable base (rounded to cents) and the grand
     total is base + IVA − retention.
   - **Given** an invoice marked not subject to IRPF **When** totals are computed **Then**
     no retention line is produced and the grand total is base + IVA.

4. Issuing an invoice assigns the next sequential number in its series atomically; numbers
   are gap-free and unique per series even under concurrent issuance (R-02, Q-1, AD-6).
   - **Given** a series whose last issued number is N **When** an invoice is issued **Then**
     it receives number N+1 and the series high-water mark advances to N+1.
   - **Given** two issuance operations racing on the same series **When** both commit
     **Then** they receive distinct consecutive numbers with no gap and no duplicate (a
     unique constraint on `(series, number)` holds and the assignment is serialized via a
     row lock / DB sequence under one transaction).

5. Issuing requires at least one valid line item and the structural mandatory fields; a
   validation failure blocks issuance and does **not** consume a series number (UC-001
   alt-flows 2a, 6a).
   - **Given** an invoice with no line items **When** issuance is attempted **Then** it is
     rejected and no number is assigned.
   - **Given** an invoice missing a structural mandatory field **When** issuance is
     attempted **Then** issuance fails inside the transaction, the transaction rolls back,
     and the series high-water mark is unchanged (the next successful issue still gets the
     untouched next number).

6. An issued invoice is immutable in its identifying/numbering fields and persists its
   recipient fiscal snapshot and computed totals, so downstream modules (T-013 record
   generation, T-016 PDF) read a stable, already-numbered record.
   - **Given** an issued invoice **When** an attempt is made to change its series number or
     issue date **Then** the change is rejected (issued invoices are append-only on those
     fields), while the persisted recipient snapshot and totals remain readable.

## Behavior Delta

How this task changes **existing product behavior** (Ring 1: `docs/`).

**Added** — behavior that did not exist before (greenfield core; no prior implementation):
- Invoice + line-item data model with `Decimal` taxable-base / IVA / IRPF / total
  calculation and per-rate-group rounding.
- Numbering **Series** model and atomic, gap-free, per-series number assignment on issue.
- Service-layer "issue invoice" action with structural validation and transactional
  rollback that does not consume a number.

**Modified** — behavior that changes; cite the Ring-1 artifact + section:
- UC-001 basic-flow steps 2–6 and alt-flows 2a/3a/6a gain a concrete fulfilling
  implementation (line items, IVA/IRPF calc, number assignment, missing-field block) —
  `docs/use-cases/UC-001-issue-compliant-invoice.md §basic-flow`.

**Removed** — n/a.

## Entities

- **Series** (new) — `invoicing/models.py` — per-business numbering series; holds prefix +
  last-issued high-water mark; owner FK.
- **Invoice** (new) — `invoicing/models.py` — header: series FK, assigned number, issue
  date, recipient fiscal snapshot, IRPF %, computed totals, issued/draft state.
- **LineItem** (new) — `invoicing/models.py` — description, quantity, unit price, IVA rate,
  invoice FK.
- **Tax/total calculator** (new) — `invoicing/calc.py` — pure `Decimal` calculation +
  per-rate-group rounding (no DB).
- **Issuance service** (new) — `invoicing/services.py` — `issue_invoice(...)`: validate +
  atomically assign next number under a transaction.
- **User** (read-only, Django auth) — owner FK on `Series`/issuer identity.
- **Compliance/Verifactu module** (read-only, future T-013) — consumer of the issued record.

## Approach

Add an `invoicing` Django app onto the T-011 skeleton. Keep calculation **pure** in
`calc.py` — `Decimal` in, grouped-and-rounded totals out, no ORM — so the R-02 arithmetic
is unit-testable in isolation. Persistence (`models.py`) carries the invoice/line-item/series
schema with a `unique_together(series, number)` invariant. Numbering lives in
`services.issue_invoice`, which opens a transaction, takes a row lock on the series (or uses
a per-series DB sequence), validates structural completeness, assigns `last+1`, and commits —
so a validation failure rolls back without consuming a number (UC-001 6a) and concurrent
issues serialize (R-02). Mirror the `models / services / calc / tests` split the
`certificates` app already established.

## Structure

**Add:**
- `invoicing/__init__.py`, `invoicing/apps.py`
- `invoicing/models.py` — `Series`, `Invoice`, `LineItem`
- `invoicing/calc.py` — pure `Decimal` taxable-base / IVA (per-rate-group) / IRPF / total
- `invoicing/services.py` — `issue_invoice(...)` (transactional, gap-free numbering)
- `invoicing/migrations/0001_initial.py`
- `invoicing/tests/` — calc (rates, rounding, IRPF on/off), numbering (sequential,
  concurrent, rollback-no-consume), issuance validation, issued-immutability

**Modify:**
- `config/settings.py` — add `"invoicing"` to `INSTALLED_APPS`
- `docs/use-cases/UC-001-issue-compliant-invoice.md` — only if review wants the basic-flow
  annotated with the implementing module (via `/openup-sync-spec`, not hand-edited here)

**Do not touch:**
- `certificates/` — T-011's app; the invoicing core does not depend on certificates.
- Verifactu record generation / hash-chain / signing — T-013 (AD-2) owns these.
- `poc/aeat-preproduccion/` — throwaway T-010 PoC.
- Client CRUD — T-015 (recipient is an inline snapshot here).

## Operations

- [ ] Scaffold the `invoicing` app and register it in `config/settings.py`; add the
      `Series`, `Invoice`, `LineItem` models with the `(series, number)` unique constraint
      and the initial migration.
- [ ] Implement `invoicing/calc.py` — pure `Decimal` calculation: per-line amount, taxable
      base grouped by IVA rate, per-group IVA rounded independently (`ROUND_HALF_UP`),
      invoice-level IRPF retention, grand total.
- [ ] Implement `invoicing/services.py` `issue_invoice(...)` — open a transaction, lock the
      series row (or use a per-series DB sequence), validate ≥1 line item + structural
      mandatory fields, assign the next gap-free number, persist; roll back without
      consuming a number on validation failure.
- [ ] Enforce issued-invoice immutability on the numbering/identifying fields (number,
      issue date) at the model layer.
- [ ] (tester) Write the calc test suite: multi-rate totals, per-rate-group rounding,
      exempt rate, IRPF on/off — assert exact `Decimal` values to the cent.
- [ ] (tester) Write the numbering test suite: sequential assignment, concurrent issuance
      (no gap / no duplicate), and validation-failure rollback proving the number is not
      consumed; confirm `python manage.py test invoicing` is green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, PR size, logging
- `docs/architecture-notebook.md` — AD-2 (compliance stays out of the core), AD-6
  (PostgreSQL transactional boundary), §2 Q-1 (compliance correctness), §4 (Invoicing core)
- `docs/project-config.yaml` — project context (Spanish invoicing domain)

> Reference, don't copy.

## Safeguards

- **Token / size budget.** `calc.py` ≤ ~120 lines; PR target < 400 lines per
  `conventions.md`. If the schema pushes past this, split tests into a follow-up.
- **Reversibility.** Pure additive — new `invoicing` app + one settings line. Back out by
  dropping the migration and removing the app from `INSTALLED_APPS`. No existing behavior
  depends on it.
- **No-go zones.** No float arithmetic in any money path — `Decimal` only (R-02). No
  Verifactu record/hash/signing logic here (AD-2/T-013). Numbering must never produce a gap
  or duplicate, and a failed issue must not consume a number. No client CRUD (T-015).
- **Compliance correctness (Q-1 / R-02).** Gap-free per-series numbering and IVA/IRPF
  arithmetic are the mitigations; they must be asserted by tests, including the concurrent
  and rollback cases — see `docs/risk-list.md` R-02.

## Verification

- `python manage.py test invoicing` passes — calc, rounding, IRPF on/off, sequential +
  concurrent numbering, and rollback-no-consume scenarios all green.
- Inspect a forced concurrent-issue test (two transactions on one series) and confirm
  distinct consecutive numbers, no gap, no duplicate.
- Grade the final spec against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-012/plan.md` exits 0.

## Success Measures

n/a — internal core with no user-facing funnel or billing surface live at this phase (no
issuance UI until a later task). The falsifiable expectation is deterministic, not a
post-release metric: **zero numbering gaps or duplicates and exact IVA/IRPF totals across
the CI suite**, including the concurrent-issuance and rollback cases (R-02 mitigation). Read
this back in CI on every run, not on a release date. *(Reason must survive review; revisit
when issuance ships to beta and a "successful-issue rate" becomes measurable.)*

## Rollout

**Flagged?** No. The invoicing core is net-new domain code reached by no user until the
issuance UI, the compliance module (T-013), and the PDF/send path (T-016) ship; there is no
existing behavior to guard and no live traffic to toggle, so a flag would add ceremony
without safety. The capability is gated naturally by being unreleased; exposure is later
controlled by environment/account access. *(Vetoable at review; if a downstream task lands a
user-facing issue screen before the rest is ready, gate it by a simple settings toggle rather
than a full flag system.)*
