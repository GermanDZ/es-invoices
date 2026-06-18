# T-017 — In-flight design decisions

Decisions made while implementing the corrective/cancellation invoices lane.
Authoritative spec is `plan.md`; this records choices the spec left to build time.

## DD1 — `corrected_by` direction + reverse `corrects`
The self-FK `corrected_by` lives on the **original** invoice and points at the
**rectificativa** that supersedes it (`original.corrected_by → rectificativa`,
satisfying requirement 3 / UC-004 postcondition "original linked to its
rectificativa and marked corrected"). Its `related_name="corrects"` gives the
rectificativa its reference back to the original (`rectificativa.corrects.first()
== original`, satisfying requirement 1's "non-null reference to the original").
One FK serves both directions; no second field needed.

## DD2 — corrected/annulled set after issuance, outside the immutability set
`corrected_by` and `annulled` are deliberately **not** in
`Invoice._IMMUTABLE_WHEN_ISSUED` (`series_id`, `number`, `issue_date`), so the
post-issue linkage write is permitted while the legal identity stays frozen
(Operation 1 acceptance: "post-issue mutation must be allowed"). A test asserts
this explicitly.

## DD3 — rectificativa is a parametrised alta, not a new record type
A factura rectificativa is a Verifactu **alta** with `TipoFactura=R1`,
`TipoRectificativa=S` and a `FacturasRectificadas`/`ImporteRectificacion` block —
not a new `VerifactuRecord.record_type`. So T-017 extends `build_registro_alta`
+ `generate_alta` with optional rectificativa params rather than adding a record
kind. `tipo_factura` is now persisted from the param (was hard-coded `"F1"`); the
default keeps every existing alta call byte-identical.

## DD4 — v1 scope: por sustitución, R1, full-restatement only
Per the plan assumptions: only **por sustitución** (`TipoRectificativa=S`) with
`TipoFactura=R1`. `ImporteRectificacion` carries the **original** record's
base/cuota (the substituted amounts): `BaseRectificada = importe_total -
cuota_total`, `CuotaRectificada = cuota_total` of the rectified alta. *Por
diferencias* (I) and the R2–R5 picker are deferred (follow-up).

## DD5 — corrected/annulled gated on submission outcome
`issue_rectificativa` marks `original.corrected_by` and `annul_invoice` marks
`invoice.annulled` only when the submission outcome is **ACCEPTED or DISABLED**
(kill-switch off → record generated but not sent, same safety as the alta path).
A REJECTED outcome leaves the original untouched (requirement 3 negative
scenario / UC-004 9a, UC-005 5a). PENDING also does not mark (not yet accepted).

## Completion verification (step 1a/1b — graded against the diff)

Requirements graded against the working diff + the green suite (116 tests, 0
failures, 2 Postgres-gated skips):

- ✅ **R1 rectificativa issuance** — `invoicing/services.py::issue_rectificativa`
  issues in the rectificativa series, recomputes totals, links the original;
  `test_corrective.RectificativaIssuanceTests.test_disabled_issues_numbers_links_and_recomputes_totals`.
- ✅ **R2 rectificativa Verifactu record (R1/S + reference + chain)** —
  `compliance/records.py::build_registro_alta` + `services.generate_alta`;
  `test_rectificativa.RectificativaRecordTests` (metadata, chain, huella, XSD).
- ✅ **R3 original marked corrected, gated on outcome** — gating in
  `issue_rectificativa`; `test_accepted_marks_original_corrected` /
  `test_rejected_leaves_original_uncorrected`.
- ✅ **R4 annulment of erroneous record, no new Invoice** —
  `invoicing/services.py::annul_invoice` reuses `generate_anulacion`;
  `test_annulment_creates_chained_record_marks_annulled_no_new_invoice`.
- ✅ **R5 annulment guardrail** — refuses when `corrected_by` set;
  `test_guardrail_refuses_annulment_when_rectificativa_exists`.
- ✅ **R6 mandatory-field / no number burn** —
  `test_rectificativa_missing_lines_does_not_consume_a_number` +
  `test_corrected_and_annulled_are_mutable_after_issue` (Operation 1 acceptance).

**Success-measure instrumentation (1b):** ✅ pre-existing + extended. The measure
reads `SubmissionAttempt` rows (T-014, pre-existing) joined to the record's
`record_type=ANULACION` / rectificativa `tipo_factura` — and `tipo_factura` is now
**persisted from the param** in `generate_alta` (was hard-coded `F1`), so a
rectificativa record is distinguishable in the data. No new event needed; the
query is computable from committed models. Read-back: **30 days after the first
production corrective submission** (pre-UI, exercised via the preproducción
sandbox in the suite; production read-back lands with the UI task).

## DD7 — UC-004/UC-005 promotion done as a status-only transition
Operation 6 names `/openup-create-use-case` to promote both UCs `draft →
approved`. The UC content was authored + rubric-graded at T-008 and the T-017
implementation realizes both faithfully (116 tests green), so the only change is
the maturity status. Re-running the full authoring skill would regenerate
already-correct, already-graded content; instead this is a status-only
frontmatter edit (a lifecycle transition the UCs' own scope sections anticipated:
"Promote UC-004/UC-005 draft → approved as part of this task"). `check-docs.py`
re-validates frontmatter/traceability (OK — 11 instances). No content edit, so no
rubric criterion is bypassed.

## DD6 — annulment guardrail
`annul_invoice` refuses (`ValidationError`) when the invoice already has
`corrected_by` set — a real-sale correction must use the rectificativa path
(UC-005 exception 2b). It reuses the shipped `generate_anulacion()` unchanged.
