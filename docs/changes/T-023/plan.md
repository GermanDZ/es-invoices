---
id: T-023
title: AEAT submission UI + outcome surfacing
status: ready
priority: high
estimate: 1 session
plan: docs/roadmap.md#construction
depends-on: [T-014, T-022]
blocks: [T-024]
touches:
  - submission
  - invoicing/views.py
  - invoicing/templates/invoicing/invoice_detail.html
  - config/urls.py
last-synced: ""
---

# T-023 — AEAT submission UI + outcome surfacing

## Story

> **As an** autónomo who has issued an invoice in FacturaSimple
> **I want** to submit its Verifactu record to the AEAT from the browser and see whether it was accepted, rejected, or is pending
> **So that** I can close the legal reporting loop without the shell or a management command

INVEST check:
✅ Independent (UI over a finished submission engine) · ✅ Negotiable (submit is a
user-triggered control, vetoable) · ✅ Valuable (makes the compliance differentiator
actor-reachable) · ✅ Estimable (one app's views/templates/url + one detail-page edit)
· ✅ Small (no engine change, no new model) · ✅ Testable (UC-002 flows are observable)

## Analysis Context

- **Domain.** The UI layer for UC-002 (submit invoice to AEAT / Verifactu). The
  `submission` app already owns the engine: `submission.services.submit_record`
  (retry / pending / persist logic) and the `SubmissionAttempt` model that records
  every outcome. T-013/T-014 built and live-sandbox-proved it; only the actor path
  is missing. This task adds views + templates + a URL surface, plus a control and
  outcome panel on the existing T-022 invoice detail page.
- **Scope boundaries.** Does NOT cover: corrective / annulment submission UI (T-024),
  the UC-004/UC-005 behaviour gaps (T-025), changing `submit_record`'s retry/persist
  logic, a background/async re-drive of `pending` attempts, bulk submission, or any
  change to issuance (T-022). No new model, no migration.
- **Definition of done.** From an issued invoice's detail page, the owner can click
  "Submit to AEAT"; the record is submitted through `submit_record`; the resulting
  `SubmissionAttempt` (accepted / rejected / pending / disabled) is surfaced with its
  AEAT message and acceptance CSV. Re-submission is guarded once accepted. All flows
  are owner-scoped and `@login_required`. Tests cover the happy path, each outcome,
  the kill-switch, and the guards.

> **Assumption:** Submission is **user-triggered** (a button on invoice detail),
> not automatic-on-issuance as UC-002's main flow narrates — the T-023 roadmap line
> explicitly scopes "a control to submit an issued invoice's record". *(Vetoable at review.)*
> **Assumption:** The control submits the invoice's **most recent `alta`
> VerifactuRecord**; an invoice with no record yet shows no submit control. *(Vetoable at review.)*
> **Assumption:** When `AEAT_SUBMISSION_LIVE` is off, the engine returns `DISABLED`
> and persists nothing; the UI reports "submission disabled in this environment" rather
> than erroring. *(Vetoable at review.)*

## Requirements

1. An issued invoice's detail page shows a **"Submit to AEAT"** control when the
   invoice has an `alta` Verifactu record and no `accepted` attempt yet.
   - **Given** an owner viewing their issued invoice that has an `alta` record and no accepted attempt
     **When** the detail page renders
     **Then** a "Submit to AEAT" submit button is present, POSTing to the submission endpoint for that invoice.
2. Submitting drives the record through `submission.services.submit_record` and
   surfaces the resulting `SubmissionAttempt` outcome.
   - **Given** the owner clicks "Submit to AEAT" and the gateway accepts
     **When** the POST completes
     **Then** a `SubmissionAttempt` with `status=accepted` is persisted by the engine and the page shows "Accepted" with the acceptance CSV.
3. A rejection is surfaced with its AEAT reason, and re-submission stays available.
   - **Given** the gateway returns a verdict of rejected
     **When** the POST completes
     **Then** the page shows "Rejected" with `aeat_code` / `aeat_message`, and the "Submit to AEAT" control remains (rejection is correctable).
4. A transport-exhausted **pending** outcome is surfaced without implying success.
   - **Given** transport fails past `AEAT_SUBMISSION_MAX_RETRIES`
     **When** the POST completes
     **Then** the page shows "Pending" with the last error message and a note that it will need re-submission.
5. The kill-switch is honored end to end.
   - **Given** `AEAT_SUBMISSION_LIVE` is off
     **When** the owner submits
     **Then** no `SubmissionAttempt` is persisted and the page reports submission is disabled in this environment.
6. Submission is owner-scoped and authenticated.
   - **Given** a logged-in user POSTs a submit for an invoice they do not own
     **When** the view resolves the invoice
     **Then** it returns 404 (no cross-owner leak); **and Given** a logged-out user **When** they GET/POST any submission URL **Then** they are redirected to login.
7. An already-accepted record cannot be re-submitted from the UI.
   - **Given** the invoice's record already has an `accepted` attempt
     **When** the owner views the detail page or POSTs a submit
     **Then** the control is absent and a re-submit POST is rejected (message + redirect, no second live call).

## Behavior Delta

**Added** — behavior that did not exist before (no prior actor-reachable path):
- Actor-triggered "Submit to AEAT" control on the invoice detail page.
- Outcome surfacing (accepted / rejected / pending / disabled + AEAT message + CSV)
  rendered for an invoice's submission attempts.

**Modified** — behavior that changes; cite the Ring-1 artifact + section:
- Realizes UC-002 as a **user-triggered** submission rather than the automatic
  "on invoice issuance" framing — `docs/use-cases/UC-002-submit-invoice-to-aeat.md §main-flow`
  (step 1–2). The stored-outcome postcondition is unchanged.

**Removed** — none.

## Success Measures

We expect the **share of newly-issued invoices that reach an `accepted`
`SubmissionAttempt` via the UI** to be **≥ 80%** within **the first 30 days** of
the feature shipping to production with `AEAT_SUBMISSION_LIVE` on — i.e. owners
actually close the reporting loop themselves rather than leaving records
unsubmitted. Instrumentation: a query over `SubmissionAttempt` joined to invoices
issued after release (`status="accepted"` per the invoice's latest `alta` record).
Read-back: **30 days after the first production release with the flag live**.

> This is honest-but-deferred: in local/preproducción the kill-switch is off, so
> the measure only becomes readable once production submission is enabled. It is
> not `n/a` because the data the UI surfaces (`SubmissionAttempt` rows) is exactly
> what makes it checkable.

## Entities

- **SubmissionAttempt** (read-only) — `submission/models.py` (status / estado / aeat_code / aeat_message / csv / retries).
- **VerifactuRecord** (read-only) — `compliance/models.py`; `invoice.verifactu_records` related set, `alta` vs `anulacion`.
- **submit_record** (read-only) — `submission/services.py`; consumed unchanged.
- **Invoice** (read-only) — `invoicing/models.py`; owner-scoped via `series__owner`.
- **Submission views/urls/templates** (new) — `submission/views.py`, `submission/urls.py`, `submission/templates/submission/`.
- **invoice_detail** (modified) — `invoicing/views.py` + its template, to pass and render submission state.

## Approach

Add a thin `submission` UI app surface that mirrors T-022's FBV + `@login_required`
+ owner-scoping conventions. A single `submission_submit(request, invoice_pk)` POST
view resolves the owner's invoice, picks its latest `alta` record, guards the
already-accepted and kill-switch cases, calls `submit_record` unchanged, and
redirects back to the invoice detail page with a `messages` outcome. The invoice
detail view/template (invoicing) is extended to load the record's attempts and
render the control + outcome panel. All compliance/retry/persist logic stays in
the engine — the view orchestrates only.

## Structure

**Add:**
- `submission/views.py` — `submission_submit` FBV (POST), owner-scoped, kill-switch + accepted guards.
- `submission/urls.py` — `app_name = "submission"`, `path("invoice/<int:invoice_pk>/submit/", ..., name="submit")`.
- `submission/templates/submission/_outcome.html` — partial rendering an attempt's status/message/CSV (included by invoice detail).
- `submission/tests/test_views.py` — flow coverage (accept/reject/pending/disabled, guards, auth, owner-scope) with a stubbed gateway.

**Modify:**
- `invoicing/views.py` — `invoice_detail` passes the latest `alta` record's attempts + a "can submit" flag.
- `invoicing/templates/invoicing/invoice_detail.html` — render the submit control + outcome panel (include the partial).
- `config/urls.py` — `path("submissions/", include("submission.urls"))`.

## Rollout

**Flagged? No new flag.** Whether submission actually reaches the AEAT is already
governed by the **permanent** `AEAT_SUBMISSION_LIVE` kill-switch (T-019 reframed it
from a temporary toggle into a permanent operational control). The UI reads that
existing control: with it **off** (default in local / preproducción per
`config/settings.py`) a submit returns `DISABLED` and the page says so; with it
**on** (production, when AEAT go-live is reached) submissions go live. Adding a
second UI-level flag would add no safety, so the control surface ships unflagged in
every environment.

- **Kill-switch behavior.** Turning `AEAT_SUBMISSION_LIVE` off mid-flight makes the
  next submit a no-op `DISABLED` outcome; no `SubmissionAttempt` is written and no
  in-flight data is corrupted (the engine short-circuits before cert/network work).
- **Flag-removal follow-up.** None — `AEAT_SUBMISSION_LIVE` is permanent
  infrastructure (T-019), not temporary debt, so there is no removal task to enqueue.

**Do not touch:**
- `submission/services.py`, `submission/aeat_direct.py`, `submission/gateway.py` — engine is consumed unchanged.
- `invoicing/services.py` — issuance/numbering is out of scope.
- `compliance/models.py` — record generation is out of scope.

## Operations

- [x] Add `submission/urls.py` (`app_name="submission"`, the `submit` route) and mount it in `config/urls.py` under `submissions/`.
- [x] Implement `submission_submit` in `submission/views.py`: `@login_required`, owner-scope the invoice (404 otherwise), select latest `alta` record, guard already-accepted and the `AEAT_SUBMISSION_LIVE` kill-switch, call `submit_record`, map the outcome to a `messages` call, redirect to `invoicing:detail`.
- [x] Extend `invoice_detail` in `invoicing/views.py` to load the latest `alta` record's `submission_attempts` and a `can_submit` flag; add the `submission/templates/submission/_outcome.html` partial and wire the submit control + outcome panel into `invoice_detail.html`.
- [x] (tester) Add `submission/tests/test_views.py` with a stubbed `SubmissionGateway`: assert accepted/rejected/pending/disabled surfacing, already-accepted + kill-switch guards, owner-scope 404, and login-required redirect.
- [x] (tester) Run `python manage.py test submission invoicing` and confirm green; fix any regressions in the touched surface only.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, change types.
- `docs/changes/archive/T-022/plan.md` — the established FBV + `@login_required` + owner-scoping + template-location UI pattern this task mirrors.
- `docs/architecture-notebook.md` — AD-3 submission interface, the `AEAT_SUBMISSION_LIVE` permanent kill-switch (T-019).

## Safeguards

- **Token / size budget.** One small app surface — view ≤ ~60 lines, partial ≤ ~40 lines, no engine edits.
- **Reversibility.** Pure-additive routes/templates plus a localized detail-view edit; revert by removing the route + control. No migration, no data change.
- **No-go zones.** `submit_record`'s retry/pending/persist logic and the kill-switch semantics must not change; submission must never bypass `AEAT_SUBMISSION_LIVE`. Issuance and numbering behavior unchanged.
- **Invariant.** The view performs no compliance logic — it only resolves ownership, guards, calls the engine, and surfaces the persisted `SubmissionAttempt`.

## Verification

- `python manage.py test submission invoicing` is green.
- Manual: as the invoice owner, the detail page of an issued invoice with an `alta`
  record shows "Submit to AEAT"; clicking it (with the flag on, gateway stubbed)
  surfaces the accepted/rejected/pending outcome; with the flag off it reports disabled.
- Logged-out access to the submit URL redirects to login; cross-owner submit 404s.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.
