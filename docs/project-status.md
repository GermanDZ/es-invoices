# Project Status

**Project**: FacturaSimple
**Phase**: construction
**Iteration**: 12
**Iteration Goal**: T-013 — Compliance/Verifactu module: record gen + hash-chain + XAdES
**Status**: completed
**Current Task**: T-013
**Started**: 2026-06-15
**Iteration Started**: 2026-06-18
**Last Updated**: 2026-06-18
**Updated By**: sync-status.py

## Notes

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
