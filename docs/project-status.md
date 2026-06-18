# Project Status

**Project**: FacturaSimple
**Phase**: construction
**Iteration**: 16
**Iteration Goal**: T-017 — Corrective / cancellation invoices (rectificativa + anulación)
**Status**: completed
**Current Task**: T-017
**Started**: 2026-06-15
**Iteration Started**: 2026-06-18
**Last Updated**: 2026-06-18
**Updated By**: sync-status.py

## Notes

- **Iteration 16** (2026-06-18): T-017 complete — corrective/cancellation invoices (S-5, REQ-004, UC-004/UC-005). Built on the shipped compliance/submission machinery: `invoicing` gains `Invoice.corrected_by` (self-FK) + `annulled` and two service orchestrators — `issue_rectificativa` (por sustitución, TipoFactura=R1/TipoRectificativa=S; clones the original, issues gap-free in a dedicated rectificativa series, generates a rectificativa-type alta referencing the original, submits, links `original.corrected_by` on accepted/disabled) and `annul_invoice` (reuses `generate_anulacion`, marks `annulled`, creates no Invoice, refuses when a rectificativa exists — UC-005 2b). `compliance.build_registro_alta`/`generate_alta` extended with rectificativa metadata (FacturasRectificadas + ImporteRectificacion, XSD-conformant); `tipo_factura` now persisted from the param (default F1 unchanged). corrected/annulled gated on the submission outcome; both excluded from the issued-immutability set. UC-004/UC-005 promoted draft→approved. 12 new tests (rectificativa record incl. XSD, issuance/linkage, annulment, guardrail, no-number-burn, post-issue mutation); full suite 116 green (2 Postgres-gated skips). No new feature flag — reaches AEAT via the existing `AEAT_SUBMISSION_ENABLED` kill-switch. Ships dark (no UI caller); acceptance read-back gated on the corrective UI task.

- **Iteration 15** (2026-06-18): T-016 complete — invoice PDF generation + send-by-email (new Django `documents` app, architecture-notebook §4 Document & delivery; S-3 / UC-001 postcondition). Read-only consumer of the invoicing core: `render_invoice_pdf` (WeasyPrint) emits all mandatory legal fields + VERI*FACTU legend + Verifactu verification QR (segno; importe/numserie/fecha sourced from persisted values matching the AEAT record); `send_invoice_email` attaches the PDF via Django's pluggable backend (console dev / SMTP prod), issued-only guard, success-instrumentation log (NumSerie only, no recipient PII / RGPD). Issuer fiscal identity passed in (no new model), mirroring `compliance.generate_alta`; ships dark (no caller wired) — delivery rate read-back gated on T-018/send UI. 12 new tests (PDF text via pypdf, email outbox, guards, read-only, instrumentation), full suite 104 green (2 Postgres-gated skips).

- **Iteration 14** (2026-06-18): T-015 complete — client/contact management (new Django `clients` app, S-1 / UC-003 / REQ-003). Owner-scoped Client model typed B2B/B2C with Spanish DNI/NIE/CIF format+checksum validation (`clients/validation.py`); type-conditional tax-id rule in `Client.clean` (B2B required, B2C optional per D-2); `@login_required` CRUD (list/create/edit/delete) with 404 cross-owner scoping; `recipient_snapshot` bridges a saved client into the invoice recipient snapshot and rejects an unusable B2B client; additive nullable `Invoice.client` provenance FK (never read by numbering/compliance). 23 client tests, full suite 92 green (2 Postgres-gated skips).

- **Iteration 13** (2026-06-18): T-014 complete — AEAT submission adapter behind the AD-3 interface (Django `submission` app). `SubmissionGateway` interface + one direct mTLS-SOAP adapter productionizing the T-010 PoC transport; `SubmissionAttempt` outcome model (accepted+CSV / rejected+code / pending); bounded transport-retry degrading to pending (no retry on business `Incorrecto`); `AEAT_SUBMISSION_ENABLED` kill-switch with preproducción-default endpoint. Cert material only via `certificates.services`; record/invoice never mutated. `aeat_submit` management command as the cert-gated preproducción smoke. 15 submission tests, full suite 69 green. Realizes UC-002.

- **Iteration 12** (2026-06-18): T-013 complete — compliance/Verifactu module (Django `compliance` app, AD-2). Versioned public API (lazy); legal-field validation; `RegistroAlta`/`RegistroAnulacion` builders + AEAT-proven `huella`; per-issuer `IssuerChain` row-lock for fork-safe chaining; XAdES-enveloped signing (signxml) verifying + tamper-failing; full `RegFactu` envelope validates against the vendored AEAT XSDs (single-rate + exempt). 17 compliance tests (1 Postgres-gated), full suite 54 green. Generates/persists signed records; submission is T-014.

- **Iteration 11** (2026-06-18): T-012 complete — invoicing core (Django `invoicing` app). Series/Invoice/LineItem models; pure-`Decimal` per-IVA-rate-group calc + invoice-level IRPF (R-02); transactional `issue_invoice` with `select_for_update` + unique `(series,number)` + bounded retry for gap-free, duplicate-free numbering; validation failure rolls back without consuming a number; issued invoices immutable on number/issue-date with recipient snapshot + totals persisted. 15 tests green (Postgres-gated true-concurrency test), full suite 37 green.

- **Iteration 10** (2026-06-18): T-011 complete — secure user-certificate upload + AES-256-GCM encrypted-at-rest storage (Django certificates app). UserCertificate model, PKCS#12 upload/validation flow, single least-privilege accessor for the AD-3 adapter (T-014), replace/delete + account cascade. 22 tests green; all six requirements graded against the diff.

- **Iteration 9** (2026-06-17): T-010 complete — AEAT `preproducción` submission PoC. All three proofs PASS against the live sandbox (prewww1.aeat.es): client-cert mTLS auth accepted; self-built F1 `alta` validated vs XSD and accepted (`Correcto`+CSV); second record hash-chained on the prior `huella` accepted with no encadenamiento error. **AD-3 BUILD-direct confirmed**, gateway-fallback not triggered; residual R-03 high→managed. Throwaway harness; secrets git-ignored.

- **Iteration 8** (2026-06-15): T-009 complete — willingness-to-pay/pricing validation (PRICE-001). Founder ratified single flat plan ~7 €/mo (~70 €/yr) + free trial (no permanent free tier in v1), 12-month paying-accounts target **150–400** (narrow after beta), Verifactu deadline treated as uncertain/tracked. Closed Vision §5 paying-accounts TODO + scope §6 pricing item; R-04 reduced to a verifiable beta validation plan. Común-territory, build-direct context unchanged.

- **Iteration 7** (2026-06-15): T-008 complete — added REQ-004 (corrective + cancellation invoices) and detailed UC-004 (factura rectificativa) + UC-005 (Verifactu anulación), distinguishing correction of a valid invoice from voiding a record sent in error. Closed the S-5/D-1 scope gap; docs validate clean. Común-territory only (no TicketBAI, N-6).

- **Iteration 6** (2026-06-15): T-007 AEAT/Verifactu submission spike complete — founder ratified **BUILD direct, PoC-gated** (gateway fallback behind the same AD-3 interface), user-supplied certificate stored securely (O-1), Verifactu común-territory only / no TicketBAI in v1 (O-3). AD-3 resolved `proposed → accepted`; architecture notebook now has no open seams. O-2 (autónomo obligation timeline) carried to construction.

- **Iteration 5** (2026-06-15): T-006 complete — architecture notebook approved; founder resolved AD-5 (Python + Django) and AD-6 (PostgreSQL). AD-3 AEAT adapter remains open, deferred to the T-007 spike.

- **Iteration 4** (2026-06-15): Authored docs/scope.md (SCOPE-001) — ratified Vision §4/§6 into an explicit v1 scope (S-1..S-6) + non-goals (N-1..N-7), with three product-owner boundary decisions: corrective invoices in scope (D-1), B2B+B2C recipients (D-2), single-user/single-business account model (D-3). Follow-up: add a requirement for facturas rectificativas in Elaboration.

- **Iteration 3** (2026-06-15): Defined top use cases UC-001 (issue compliant invoice), UC-002 (submit to AEAT/Verifactu), UC-003 (manage client), each tracing from new draft requirements REQ-001..003 (← VIS-001). 7 instances validate; coverage clean (draft reqs carry no test expectation yet).

- **Iteration 2** (2026-06-15): Drafted docs/risk-list.md — 8 risks ranked by exposure, each with trigger + verifiable mitigation + owner; highest live exposures R-03 (AEAT integration) and R-04 (adoption/willingness to pay). Traces from vision §6–§7.

- **Iteration 1** (2026-06-15): Authored docs/vision.md for FacturaSimple via guided Q&A — compliance-first/Verifactu-native invoicing for autónomos & small pymes; north-star metric = time-to-first-invoice < 5 min. All 8 vision-rubric sections filled (TODOs: tech stack, paying-accounts target).
