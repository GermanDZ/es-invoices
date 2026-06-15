# Project Status

**Project**: FacturaSimple
**Phase**: elaboration
**Iteration**: 8
**Iteration Goal**: T-009 — Willingness-to-pay / pricing validation (close Vision §5 TODO, address R-04)
**Status**: in-progress
**Current Task**: T-009
**Started**: 2026-06-15
**Iteration Started**: 2026-06-15
**Last Updated**: 2026-06-15
**Updated By**: openup-start-iteration

## Notes

- **Iteration 7** (2026-06-15): T-008 complete — added REQ-004 (corrective + cancellation invoices) and detailed UC-004 (factura rectificativa) + UC-005 (Verifactu anulación), distinguishing correction of a valid invoice from voiding a record sent in error. Closed the S-5/D-1 scope gap; docs validate clean. Común-territory only (no TicketBAI, N-6).

- **Iteration 6** (2026-06-15): T-007 AEAT/Verifactu submission spike complete — founder ratified **BUILD direct, PoC-gated** (gateway fallback behind the same AD-3 interface), user-supplied certificate stored securely (O-1), Verifactu común-territory only / no TicketBAI in v1 (O-3). AD-3 resolved `proposed → accepted`; architecture notebook now has no open seams. O-2 (autónomo obligation timeline) carried to construction.

- **Iteration 5** (2026-06-15): T-006 complete — architecture notebook approved; founder resolved AD-5 (Python + Django) and AD-6 (PostgreSQL). AD-3 AEAT adapter remains open, deferred to the T-007 spike.

- **Iteration 4** (2026-06-15): Authored docs/scope.md (SCOPE-001) — ratified Vision §4/§6 into an explicit v1 scope (S-1..S-6) + non-goals (N-1..N-7), with three product-owner boundary decisions: corrective invoices in scope (D-1), B2B+B2C recipients (D-2), single-user/single-business account model (D-3). Follow-up: add a requirement for facturas rectificativas in Elaboration.

- **Iteration 3** (2026-06-15): Defined top use cases UC-001 (issue compliant invoice), UC-002 (submit to AEAT/Verifactu), UC-003 (manage client), each tracing from new draft requirements REQ-001..003 (← VIS-001). 7 instances validate; coverage clean (draft reqs carry no test expectation yet).

- **Iteration 2** (2026-06-15): Drafted docs/risk-list.md — 8 risks ranked by exposure, each with trigger + verifiable mitigation + owner; highest live exposures R-03 (AEAT integration) and R-04 (adoption/willingness to pay). Traces from vision §6–§7.

- **Iteration 1** (2026-06-15): Authored docs/vision.md for FacturaSimple via guided Q&A — compliance-first/Verifactu-native invoicing for autónomos & small pymes; north-star metric = time-to-first-invoice < 5 min. All 8 vision-rubric sections filled (TODOs: tech stack, paying-accounts target).
