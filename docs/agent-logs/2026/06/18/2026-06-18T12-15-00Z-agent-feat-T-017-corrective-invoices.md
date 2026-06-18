# Agent Run Log — T-017 (promote → implement → complete, single cycle)

- **Task:** T-017 — Corrective / cancellation invoices (rectificativa + anulación)
- **Branch:** feat/T-017-corrective-invoices
- **Phase:** construction · **Track:** standard · **Iteration:** 16
- **Start:** 2026-06-18T12:02:06Z · **End:** 2026-06-18T12:15:00Z

## Commits (vs trunk origin/main)
- `89e4109` docs(T-017): promote roadmap task to REASONS-Canvas spec
- `edff674` feat(T-017): corrective + cancellation invoices (rectificativa + anulación)
- (`bff5ff4` chore(process): sweep run-log shards — pre-existing local trunk commit, carried along)

## Files changed
- `invoicing/models.py` — `Invoice.corrected_by` (self-FK, related_name `corrects`) + `annulled`; both kept out of `_IMMUTABLE_WHEN_ISSUED`.
- `invoicing/migrations/0003_invoice_annulled_invoice_corrected_by.py`
- `invoicing/services.py` — `issue_rectificativa()` (por sustitución, R1) + `annul_invoice()` orchestrators; `_original_alta()` helper.
- `compliance/records.py` — `build_registro_alta()` rectificativa params (TipoRectificativa, FacturasRectificadas, ImporteRectificacion); `tipo_factura` parametrised.
- `compliance/services.py` — `generate_alta()` threads rectificativa metadata; persists `tipo_factura` from the param.
- `compliance/tests/test_rectificativa.py`, `invoicing/tests/test_corrective.py` — 12 new tests.
- `docs/use-cases/UC-004…`, `UC-005…` — status draft → approved.
- `docs/changes/T-017/{plan.md,design.md}` — spec, ticked Ops, DD1–DD7 + completion grade, `touches`.

## Decisions (design.md DD1–DD7)
- DD1: `corrected_by` on the original → rectificativa; reverse `corrects` gives the rectificativa→original reference (one FK, both directions).
- DD3: rectificativa = parametrised *alta* (TipoFactura=R1), not a new record_type; default F1 keeps every existing alta byte-identical.
- DD4: v1 scope por sustitución / R1 only; ImporteRectificacion carries the original's base/cuota.
- DD5: corrected/annulled marked only on ACCEPTED or DISABLED (kill-switch off); REJECTED leaves the original untouched.
- DD6: annulment refuses when `corrected_by` is set (UC-005 2b).
- DD7: UC promotion done as a status-only transition (content rubric-graded at T-008, realized faithfully).

## Outcome
- `manage.py test` → 116 passed, 2 Postgres-gated skips; `makemigrations --check` clean.
- All six requirements graded ✅ against the diff; success-measure instrumentation ✅ (pre-existing `SubmissionAttempt` + `tipo_factura`/`record_type`); not flagged (reuses `AEAT_SUBMISSION_ENABLED`).
- Write-fence exit 0 (13 files in-lane); check-docs OK (11 instances, coverage clean).

## Process note (recurring friction — known memory)
- The promote path again hit `gate-edits.py`: `gates.plan_persisted` is left `false`
  by start-iteration for a `docs/changes` spec, blocking the first source edit until
  set manually (`openup-state.py set-gate plan_persisted <plan path>`). Matches the
  standing learning; framework follow-up still open.
