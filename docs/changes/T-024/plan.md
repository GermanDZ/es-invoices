---
id: T-024
title: Corrective & annulment UI (rectificativa + anulación)
status: ready   # proposed → ready → in-progress → done → verified
priority: medium   # critical | high | medium | low
estimate: 1–2 sessions
plan: docs/roadmap.md#construction
depends-on: [T-017, T-023]
blocks: []
last-synced: ""
touches:
  - invoicing/views.py
  - invoicing/urls.py
  - invoicing/forms.py
  - invoicing/templates/invoicing/
  - invoicing/tests/
  - docs/changes/T-024/
---

# T-024 — Corrective & annulment UI (rectificativa + anulación)

## Story

> **As an** autónomo who already issued an invoice
> **I want** to issue a *factura rectificativa* to correct it, or *anular* a record raised in error, from the invoice page
> **So that** I can complete the legally-required correction workflows myself without touching code or the database.

INVEST check:
✅ Independent (engine verbs already shipped by T-017) · ✅ Negotiable · ✅ Valuable (closes the actor path for UC-004/UC-005) · ✅ Estimable · ✅ Small (UI over existing services) · ✅ Testable (view-level request/response + outcome surfacing)

## Analysis Context

State the *why* the spec needs but the code can't show:

- **Domain.** The browser/actor layer for the two correction workflows in the
  `invoicing` app. The compliance engine is **already built and tested** (T-017):
  `invoicing.services.issue_rectificativa(rectificativa, original, *, issuer_nif,
  issuer_name, tipo_factura="R1", …)` (UC-004, *por sustitución*) and
  `invoicing.services.annul_invoice(invoice, *, issuer_name, …)` (UC-005). Both
  generate the Verifactu record, submit via the AD-3 gateway, and persist the
  outcome. **This task adds no engine logic** — only views, forms, templates, and
  URLs that drive those verbs, mirroring the issuance UI (T-022,
  `invoicing/views.py`) and the submission UI (T-023, `submission/views.py`).
- **Scope boundaries.** This task does NOT:
  - implement the *por diferencias* method (the engine hardcodes
    `tipo_rectificativa="S"`) — **T-025** owns that gap;
  - mark the rectificativa PDF as such or print the corrected-invoice reference —
    **T-025** (UC-004 postcondition);
  - implement UC-005 alt-flow 2a (annul-while-pending cancels the pending
    submission) — the engine has no such path yet; **T-025** owns it;
  - exclude annulled invoices from any "active set" list view — **T-025**;
  - add `Client.email` — **T-025**;
  - touch the engine services, compliance, or submission modules' logic.
  It surfaces *only* what the shipped engine supports today.
- **Definition of done.** From an owned, issued invoice's detail page the user can:
  (a) open a rectificativa form pre-filled from the original, pick the correction
  type (R1–R5), edit the restated line items, review the recomputed totals, confirm,
  and see the AEAT outcome; (b) open an annul-confirm page carrying the UC-005 step-2
  warning, confirm, and see the AEAT outcome. Engine `ValidationError`s (e.g. annul
  refused because the invoice has a rectificativa — UC-005 2b) are surfaced as
  messages, never 500s. All paths owner-scoped (`series__owner=request.user`).

> **Assumption:** the UC-004 "reason/type of correction" selector is the Verifactu
> rectificativa subtype `tipo_factura` (R1–R5, the engine's existing parameter),
> labelled in plain language; the corrective restates the full corrected invoice
> (*por sustitución*, the only method the engine supports). *(Vetoable at review.)*
> **Assumption:** the rectificativa is issued into a dedicated series obtained via
> `Series.objects.get_or_create(owner=user, prefix="R")`, reusing the gap-free
> numbering guarantee — distinct from the ordinary series so original and corrective
> numbers never collide. *(Vetoable at review.)*
> **Assumption:** the rectificativa form pre-fills its line items from the original
> invoice's line items (editable), matching UC-004 basic-flow step 3. *(Vetoable at review.)*

## Requirements

1. From an owned, issued, not-yet-corrected invoice's detail page, a "Rectificar"
   action opens a rectificativa form pre-filled from the original.
   - **Given** an issued invoice owned by the logged-in user that has no
     `corrected_by` set **When** the user opens its detail page **Then** a
     "Rectificar (emitir factura rectificativa)" link to the rectificativa form is
     shown, and the form is pre-filled with the original's line items and recipient.

2. Submitting the rectificativa form drives `issue_rectificativa`, issuing the
   corrective in the rectificativa series and linking the original.
   - **Given** the rectificativa form with a chosen type (R1–R5) and edited line
     items **When** the user confirms issuance and the AEAT accepts (or submission
     is disabled) **Then** a new rectificativa invoice is persisted in the `R`
     series, `original.corrected_by` points to it, and the user is redirected to
     the rectificativa's detail page with a success message.

3. The view never assigns numbers, computes totals, or calls the AEAT itself — it
   builds the draft and delegates to `invoicing.services.issue_rectificativa`.
   - **Given** a valid rectificativa submission **When** it is processed **Then**
     the only numbering/record/submission calls are inside `issue_rectificativa`
     (the view assigns no `number` and makes no gateway call), verified by the
     rectificativa carrying an `R`-series number and a linked Verifactu record.

4. An engine `ValidationError` (e.g. original not issued, no alta record) rolls the
   draft back and re-renders the form with the message; no series number is consumed.
   - **Given** a rectificativa attempt whose engine precondition fails **When** the
     POST is processed **Then** the response re-renders the form showing the error
     message and the `R` series `last_number` is unchanged.

5. From an owned, issued invoice's detail page, an "Anular (emitida por error)"
   action opens a confirmation page carrying the UC-005 step-2 warning.
   - **Given** an issued invoice owned by the user **When** the user opens the
     annul page **Then** it displays the warning that annulment is only for records
     sent in error (redirecting genuine corrections to a rectificativa) and requires
     an explicit confirm before any action.

6. Confirming the annulment drives `annul_invoice`, and the outcome is surfaced.
   - **Given** the annul confirmation **When** the user confirms and the AEAT
     accepts (or submission is disabled) **Then** `invoice.annulled` is `True` and
     the user is redirected to the invoice detail with a success message.

7. When the engine refuses an annulment because the invoice carries a rectificativa
   (UC-005 exception 2b), the refusal is surfaced as a message, not a 500.
   - **Given** an invoice whose `corrected_by` is set **When** the user POSTs the
     annul confirmation **Then** the `ValidationError` is caught and shown as an
     error message steering the user to a rectificativa, and `invoice.annulled`
     stays `False`.

8. Every rectificativa/annul view is owner-scoped: a cross-owner invoice pk is a 404.
   - **Given** an invoice whose series owner is a different user **When** the
     logged-in user requests its rectificativa form or annul page (GET or POST)
     **Then** the response is HTTP 404 and no engine verb runs.

## Behavior Delta

How this task changes **existing product behavior** (Ring 1).

This task realizes two **already-approved** use cases that no actor could previously
reach (the engine shipped in T-017, but there was no UI). Realizing an
approved-but-unimplemented use case is *Added* actor behavior, not a *Modified*
redefinition — UC-004/UC-005 content is unchanged.

**Added** — behavior that did not exist before (no prior actor path):
- A browser path (detail-page "Rectificar" action → form → confirm) to issue a
  *factura rectificativa*, *por sustitución* — realizes the approved basic flow of
  `docs/use-cases/UC-004-issue-corrective-invoice.md §basic-flow`.
- A browser path (detail-page "Anular" action → warning/confirm page) to *anular* a
  record raised in error — realizes the approved basic flow of
  `docs/use-cases/UC-005-annul-invoice-record.md §basic-flow`, including the
  step-2 warning.

**Modified** — none. UC-004/UC-005 spec content is untouched; this lane changes no
existing, already-reachable product behavior.

**Removed** — none.

> The remaining UC-004/UC-005 acceptance gaps (por diferencias, PDF marking,
> annul-while-pending, active-set exclusion) are *spec-conformance debt* owned by
> **T-025** (`docs/roadmap.md`), not a behavior change introduced here — so no
> `/openup-sync-spec` back-propagation is due from this lane.

## Success Measures

We expect **the share of issued invoices that are corrected/annulled through the
UI rather than via shell/DB** to reach **≥ 95% of all correction events** within
**the first 30 days** any correction workflow is exercised post-release.
Instrumentation: count `Invoice` rows with `corrected_by` set or `annulled=True`
created/updated through the new views (request log / a `SubmissionAttempt` whose
record is a rectificativa-alta or anulación) versus any correction state changed
out-of-band. Read-back: 30 days after the first production correction, or at the
next phase review — whichever is first.

(Honest caveat: at pre-beta volume this may be `n/a — no production correction
traffic yet`; the measure is stated so it can be read back once beta users exist.)

## Entities

- **`invoice_rectificar` view** (new) — `invoicing/views.py`
- **`invoice_annul` view** (new) — `invoicing/views.py`
- **`RectificativaForm`** (new, type selector R1–R5 + reuses `LineItemFormSet`) — `invoicing/forms.py`
- **rectificativa / annul templates** (new) — `invoicing/templates/invoicing/`
- **`invoice_detail.html`** (modified — adds the two action links) — `invoicing/templates/invoicing/invoice_detail.html`
- **`invoicing/urls.py`** (modified — two routes) — `invoicing/urls.py`
- **`issue_rectificativa` / `annul_invoice`** (read-only — drive, do not change) — `invoicing/services.py`
- **`_surface_outcome` / `submission/_outcome.html`** (read-only — reuse for outcome messaging) — `submission/views.py`, `submission/templates/submission/_outcome.html`

## Approach

Add two owner-scoped views to `invoicing/views.py` that mirror the T-022 issuance
and T-023 submission patterns: resolve the invoice through
`_owner_invoices(request.user)`, build the draft / read the confirm, then delegate
entirely to the shipped engine verb and surface the outcome. The rectificativa view
reuses the issuance line-item formset (pre-filled from the original) plus a small
`tipo_factura` (R1–R5) selector, obtains the `R` series, and calls
`issue_rectificativa`; the annul view is a GET warning page + POST confirm calling
`annul_invoice`. Outcome messaging reuses the submission app's `_surface_outcome`
helper so accepted/rejected/pending/disabled read identically to T-023. No engine,
compliance, or submission *logic* is touched.

## Structure

**Add:**
- `invoicing/templates/invoicing/rectificativa_form.html`
- `invoicing/templates/invoicing/annul_confirm.html`
- `invoicing/tests/test_rectificativa_view.py`
- `invoicing/tests/test_annul_view.py`

**Modify:**
- `invoicing/views.py` — add `invoice_rectificar` and `invoice_annul` views (+ helpers)
- `invoicing/forms.py` — add `RectificativaForm` (R1–R5 type selector); reuse `LineItemFormSet`
- `invoicing/urls.py` — add `rectificar` and `annul` routes
- `invoicing/templates/invoicing/invoice_detail.html` — add the two action links (shown per state)

**Do not touch:**
- `invoicing/services.py`, `compliance/`, `submission/services.py` — engine logic is T-017's; this lane only calls it.
- The *por diferencias* path, PDF rectificativa marking, annul-while-pending, active-set exclusion, `Client.email` — all **T-025**.

## Operations

- [ ] Add `RectificativaForm` to `invoicing/forms.py` — a `tipo_factura` choice field (R1–R5 with plain-language labels) reusing `LineItemFormSet`; add a helper to pre-fill the formset from an original invoice's line items.
- [ ] Add `invoice_rectificar(request, pk)` to `invoicing/views.py`: owner-scope the original, GET pre-fills the form from it; POST builds the draft rectificativa in the `R` series (`get_or_create`) and calls `issue_rectificativa`, catching `ValidationError` to re-render, surfacing the outcome, and redirecting to the rectificativa's detail on success.
- [ ] Add `invoice_annul(request, pk)` to `invoicing/views.py`: owner-scope the invoice, GET renders the UC-005 step-2 warning page, POST calls `annul_invoice` catching `ValidationError` (UC-005 2b) and surfacing the outcome, then redirects to detail.
- [ ] Add `rectificar` and `annul` routes to `invoicing/urls.py`; add `rectificativa_form.html` and `annul_confirm.html` templates and the two action links (state-gated) to `invoice_detail.html`.
- [ ] (tester) Write `test_rectificativa_view.py` and `test_annul_view.py` covering Requirements 1–8: pre-fill, happy-path link/redirect, engine-`ValidationError` rollback, the UC-005 2b refusal message, and the cross-owner 404 — using the in-memory/disabled gateway so no live AEAT call is made.
- [ ] (tester) Run the full `invoicing` + `submission` test suites and confirm green; record results in `docs/changes/T-024/design.md`.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `invoicing/views.py`, `submission/views.py` — established view/owner-scoping/outcome-surfacing patterns this lane mirrors.
- `docs/architecture-notebook.md` — AD-3 (submission interface), gap-free numbering (S-2).

## Safeguards

- **No engine changes.** `invoicing/services.py`, `compliance/`, and
  `submission/services.py` logic must be byte-unchanged — the views only call the
  shipped verbs. (No-go zone.)
- **Owner-scoping invariant.** Every view resolves the invoice through
  `series__owner=request.user`; a cross-owner pk is a 404 on GET and POST.
- **No live AEAT in tests.** Tests run with the gateway disabled / in-memory
  (`AEAT_SUBMISSION_LIVE` off or an injected gateway) — never a real network call.
- **Numbering authority.** The view assigns no invoice `number` and computes no
  totals; `issue_rectificativa` → `issue_invoice` remains the sole numbering
  authority, and a rolled-back draft consumes no series number.
- **Reversibility.** New views/routes/templates; revert is deleting the additions
  and the two `invoice_detail.html` links. No migrations, no data changes.
- **Token / size budget.** Each new view ≤ ~40 lines; no new model fields.

## Rollout

**Flagged?** No. Reason: this is additive UI (new views/routes/templates) that
calls already-shipped engine verbs. The only safety-relevant toggle —
`AEAT_SUBMISSION_LIVE` — already gates whether the rectificativa/annulment records
actually reach the AEAT, and it is owned by T-019/T-023; this UI inherits it
unchanged. A new feature flag would add no safety the existing kill-switch and the
owner-scoped `@login_required` views don't already provide, and the actions are
discoverable only from an owned invoice's detail page. Kill path if needed: remove
the two `invoice_detail.html` action links (the routes become unreachable from the
UI) — no data migration. No flag ⇒ no flag-removal follow-up.

## Verification

- `python manage.py test invoicing submission` — green, including the new
  `test_rectificativa_view.py` / `test_annul_view.py`.
- Manual: as a logged-in owner, issue an invoice → "Rectificar" → confirm → land on
  the rectificativa detail with the AEAT outcome; issue another → "Anular" → see the
  warning → confirm → invoice shows annulled. A cross-owner pk 404s.
- `git diff` shows no change under `invoicing/services.py`, `compliance/`, or
  `submission/services.py`.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.
