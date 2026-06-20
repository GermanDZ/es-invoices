# T-023 — In-flight design decisions

- **DD1 — Read helpers live in a new `submission/selectors.py`, not in
  `services.py` or `views.py`.** Both the new `submission_submit` view and the
  extended `invoicing.invoice_detail` need "latest `alta` record for an invoice"
  and "is this record already accepted". Putting them in `selectors.py` keeps
  `submission/services.py` untouched (Structure "Do not touch") and lets
  `invoicing.views` import a pure query helper instead of another view module.
  Acyclic: `selectors` imports only `compliance.models` + `submission.models`.

- **DD2 — DISABLED uses the *returned* outcome, not a persisted attempt.**
  `submit_record` returns `DISABLED` and writes **no** `SubmissionAttempt` when
  `AEAT_SUBMISSION_LIVE` is off. So the immediate post-submit message is derived
  from the returned `SubmissionOutcome`; the detail-page outcome panel renders the
  persisted attempts (which is correctly empty in the disabled case).

- **DD3 — Submit is POST-only and idempotent-guarded.** The view redirects GET to
  the detail page, and refuses to re-submit a record that already has an
  `accepted` attempt (Requirement 7) before calling the engine — so the guard
  never makes a second live call.

## Completion verification (step 1a — each requirement vs the diff)

- ✅ **R1** (control shown when alta record + not accepted) — `invoice_detail`
  passes `submission_can_submit`; `_outcome.html` renders the button under
  `{% if submission_can_submit %}`. Test: `test_control_present_for_unsubmitted_record`.
- ✅ **R2** (drives `submit_record`, surfaces accepted + CSV) — `submission_submit`
  → `submit_record`; `_surface_outcome` ACCEPTED + panel CSV. Test:
  `test_accepted_persists_attempt_and_shows_receipt`.
- ✅ **R3** (rejection reason surfaced, control remains) — `_surface_outcome`
  REJECTED with code/message; `can_submit` unchanged. Test:
  `test_rejected_surfaces_reason_and_keeps_control`.
- ✅ **R4** (pending surfaced, no false success) — `_surface_outcome` PENDING
  `messages.warning`. Test: `test_pending_surfaces_without_implying_success`.
- ✅ **R5** (kill-switch honored end to end) — flag off → engine `DISABLED`, no
  attempt; info message. Test: `test_disabled_writes_no_attempt`.
- ✅ **R6** (owner-scoped + authenticated) — `Invoice.objects.filter(series__owner)`
  404 + `@login_required`. Tests: `test_cross_owner_submit_is_404`,
  `test_anonymous_is_redirected_to_login`.
- ✅ **R7** (accepted record not re-submittable) — control absent + POST guard
  before engine call. Tests: `test_control_absent_once_accepted`,
  `test_already_accepted_does_not_resubmit`.

Full suite: 161 tests green (2 Postgres-gated skips).

## Success-measure instrumentation (step 1b)

- ✅ **Instrumentation exists** — the measure ("share of issued invoices reaching
  an `accepted` `SubmissionAttempt` via the UI") is read from the
  `SubmissionAttempt` table (pre-existing, `submission/models.py`, T-014). This
  task makes those rows **actor-created**: `submission_submit` → `submit_record`
  persists them. The query joins `SubmissionAttempt(status="accepted")` to the
  invoice's latest `alta` record — both already persisted.
- **Read-back date:** 30 days after the first production release with
  `AEAT_SUBMISSION_LIVE` on (deferred — unreadable until production go-live, by
  design; not `n/a` because the underlying data is committed).
