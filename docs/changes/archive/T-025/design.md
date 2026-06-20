# T-025 — Design Decisions & Completion Verification

## In-flight decisions

- **DD1 — método as a service param, not a new UI form.** `issue_rectificativa`
  gained `method="S"` (back-compatible default) that flows straight to
  `compliance.generate_alta(tipo_rectificativa=...)`, which already supports both
  "S"/"I". The UI exposes it as a single `metodo` selector on `RectificativaForm`
  (`{{ form.as_p }}` renders it automatically — no template edit). Line-item entry
  is identical for both methods (spec assumption), so no delta-only UI was built.
- **DD2 — annul-while-pending returns `(None, None)`.** The pending-cancel branch
  generates no record and submits nothing, so there is no `(record, outcome)` to
  return. The annul view treats `outcome is None` as the cancel path and shows a
  dedicated success message. This kept all view changes inside `invoicing/views.py`
  — no new `SubmissionStatus` member and no edit to `submission/views.py`/`gateway.py`.
- **DD3 — `cancelled` status owned by submission.** Added `SubmissionAttempt.CANCELLED`
  to submission's vocabulary (a choices-only `AlterField`, no schema change) so
  `invoicing` references `SubmissionAttempt.CANCELLED` rather than inventing the
  string — keeps the rule behind its module (safeguard).
- **DD4 — `touches` corrected at authoring time.** The spec's Entities section named
  a lightweight write to `submission/models.py` but the `touches` frontmatter omitted
  `submission/`. Added `submission/models.py` + `submission/migrations/` to `touches`
  and re-claimed, per the `promoted-spec-missing-touches-blocks-fence` learning.
- **DD5 — `active()` via a custom `InvoiceQuerySet` manager.** No consumer listing
  screen exists yet (out of scope); the canonical selector + test is the deliverable.
  Annulled records are excluded from listings only — direct detail/pdf access stays
  reachable via the same default manager.

## Completion verification (step 1a) — graded against the diff + green tests

- ✅ **R1 (por-diferencias reachable)** — `invoicing/services.py` `method` param →
  `generate_alta(tipo_rectificativa=method)`; `invoicing/forms.py` `metodo` selector;
  `invoicing/views.py` threads `form.cleaned_data["metodo"]`. Verified by
  `test_corrective.test_method_por_diferencias_sets_tipo_rectificativa_I_no_importe`,
  `…test_default_method_is_sustitucion_S`, and the view test
  `test_rectificativa_view.test_post_por_diferencias_threads_method_to_record`.
- ✅ **R2 (rectificativa PDF marked + cites NumSerie)** — `documents/services.py`
  computes `corrected`/`corrected_num_serie` (read-only); `invoice.html` renders the
  *Factura rectificativa* marking + reference. Verified by
  `test_pdf.RectificativaMarkingTests` (present for a rectificativa, absent for an
  ordinary invoice).
- ✅ **R3 (annul-while-pending)** — `invoicing/services.py annul_invoice` forks on the
  alta's latest `SubmissionAttempt`: pending → cancel attempt + annul locally + no
  anulación; accepted/disabled → unchanged. Verified by
  `test_corrective.AnnulmentTests.test_annul_while_pending_cancels_attempt_and_sends_no_anulacion`
  and `…test_annul_when_accepted_generates_anulacion`.
- ✅ **R4 (active-set exclusion)** — `invoicing/models.py InvoiceQuerySet.active()`
  excludes `annulled=True`. Verified by `test_corrective.ActiveSetTests` and the
  record-still-reachable check `test_annul_view.test_annulled_invoice_detail_still_loads`.
- ✅ **R5 (recipient email)** — `clients/models.py Client.email` (optional EmailField)
  + `clients/forms.py` field; `documents.services._recipient_email` already resolves it
  via `getattr`. Verified by `clients.tests.test_email.ClientEmailFormTests` (valid /
  invalid / empty) and `documents.tests.test_email.ResolvesClientEmailTests`.

**All five requirements ✅. Full suite: `Ran 185 tests … OK (skipped=2)`** (2
Postgres-gated skips). No missing migrations.

## Success-measure instrumentation (step 1b)

`n/a — pre-launch spec-conformance debt` (no live users in Construction; the value
is closing approved-use-case acceptance criteria, verified by the R1–R5 tests above).

## Rollout

`n/a — no new flag` (conformance corrections; the existing permanent
`AEAT_SUBMISSION_LIVE` kill-switch is unchanged). No flag-removal row required.
