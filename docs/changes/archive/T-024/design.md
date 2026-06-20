# T-024 — design notes (in-flight decisions)

Lane: corrective & annulment UI (rectificativa + anulación). UI-over-engine — the
T-017 verbs `invoicing.services.issue_rectificativa` / `annul_invoice` are driven
as-is; no engine/compliance/submission logic changed.

## Decisions

- **DD1 — Issuer identity in `RectificativaForm`, carried in session.** The engine
  verb needs `issuer_nif` + `issuer_name`, which the original may not have left in
  the session (a correction often happens a session later). So `RectificativaForm`
  collects the issuer block inline (prefilled from the session via `_issuer_initial`,
  re-stored on success), mirroring `IssuanceForm`/T-022 DD1 exactly rather than
  dead-ending on an empty session. This extends the spec's "type selector + formset"
  description with the issuer fields the engine call requires — an implementation
  detail, not a change to UC-004 acceptance criteria.
- **DD2 — Rectificativa recipient/IRPF copied from the original.** *Por sustitución*
  restates the corrected invoice, so the draft snapshots `recipient_name/taxid/address`,
  `client`, and `irpf_rate` from the original; the user edits only the corrected line
  items (pre-filled via `lineitem_initial_from`). No client re-selection.
- **DD3 — `R`-prefixed rectificativa series via `get_or_create`.** Distinct from the
  ordinary series so original and corrective numbers never collide; reuses the
  gap-free numbering guarantee. The `get_or_create` sits *outside* the issuance
  `transaction.atomic()` so a rolled-back (non-issuable) draft leaves the series row
  present with `last_number` unchanged — Requirement 4.
- **DD4 — Outcome surfacing reuses T-023.** Both views surface the AEAT outcome via
  `submission.views._surface_outcome` (accepted/rejected/pending/disabled wording
  identical to T-023). Django messages survive the redirect, so the rectificativa
  success path messages the outcome and lands on the new invoice's detail, whose
  `_outcome.html` panel also shows the persisted attempt.
- **DD5 — IVA pre-fill string match.** Stored `iva_rate` is `Decimal("21.00")` but the
  choice values are `"21"`; `lineitem_initial_from` maps by numeric equality against
  `calc.IVA_RATES` so the pre-filled row selects the right option.

## Scope held to the engine's current capability (gaps → T-025)

*Por diferencias* (engine hardcodes `tipo_rectificativa="S"`), rectificativa PDF
marking + corrected-invoice reference, annul-while-pending (UC-005 alt 2a),
active-set exclusion of annulled invoices, and `Client.email` are **not** in this
lane — all owned by T-025. The `tipo_factura` selector exposes R1–R5 (the engine's
existing parameter); the method stays *por sustitución*.

## Tests / results

- New: `invoicing/tests/test_rectificativa_view.py` (6), `test_annul_view.py` (5) —
  cover Requirements 1–8: detail-link presence, pre-fill, happy-path issue/link/redirect,
  engine-`ValidationError` rollback with no number burned, already-corrected guard,
  UC-005 2b refusal-as-message, and cross-owner 404 on GET+POST.
- `manage.py test invoicing submission` → **74 OK** (1 Postgres-gated skip).
- Full suite `manage.py test` → **172 OK** (2 skips). No live AEAT call (kill-switch
  off by default → DISABLED outcome; engine still marks corrected/annulled).

## Completion verification (step 1a — graded against the diff)

- ✅ **Req 1** (entry + pre-fill) — `invoice_detail.html` state-gated "Rectificar" link;
  `invoice_rectificar` GET seeds `LineItemFormSet(initial=lineitem_initial_from(original))`.
  Tests: `test_detail_shows_rectificar_link…`, `test_get_form_prefilled_from_original`.
- ✅ **Req 2** (issue in `R` series + link original) — `_rectify_from_forms` →
  `issue_rectificativa`; redirect to `invoicing:detail` of the new rect. Test:
  `test_post_issues_rectificativa_in_R_series_and_links_original` (asserts `R` prefix,
  `original.corrected_by_id == rect.id`).
- ✅ **Req 3** (view delegates; never numbers/calls AEAT) — view assigns no `number`,
  makes no gateway call; numbering/record inside `issue_rectificativa`. Same test asserts
  `rect.number == rect.series.last_number` and a `verifactu_records` row exists.
- ✅ **Req 4** (ValidationError rollback, no number burned) —
  `test_engine_validationerror_rerenders_and_burns_no_number` (200 re-render, `R`
  `last_number == 0`, no new Invoice, `corrected_by` None).
- ✅ **Req 5** (annul warning page) — `invoice_annul` GET → `annul_confirm.html`;
  `test_get_renders_warning_and_confirm` (contains "error" + "Confirmar", no change on GET).
- ✅ **Req 6** (confirm annuls) — POST → `annul_invoice`; `test_post_marks_annulled_and_redirects`.
- ✅ **Req 7** (UC-005 2b refused as message, not 500) —
  `test_post_on_corrected_invoice_is_refused_as_message_not_500` (redirect, `annulled` False).
- ✅ **Req 8** (owner-scoping 404) — both views `get_object_or_404(_owner_invoices(...))`;
  `test_cross_owner_is_404` in both files (GET+POST 404, no state change).

**All 8 ✅.** No ❌ — completion unblocked.

## Success-measure instrumentation (step 1b)

`n/a — no production correction traffic yet` (argued in the spec's caveat). The
underlying signals the measure names already exist (`Invoice.corrected_by` /
`Invoice.annulled` fields; `submission.SubmissionAttempt` rows), but the
"via-UI vs out-of-band" split is not separately instrumented and would be vanity
at pre-beta volume. Read-back deferred to the first production correction / next
phase review, per the spec.
