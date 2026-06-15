# Project Status

**Project**: FacturaSimple
**Phase**: construction
**Iteration**: 8
**Iteration Goal**: —
**Status**: phase-initiated (ready to start T-010)
**Current Task**: —
**Started**: 2026-06-15
**Iteration Started**: 2026-06-15
**Last Updated**: 2026-06-15
**Updated By**: openup-quick-task (construction backlog seed)

## Notes

- **Phase transition → Construction** (2026-06-15): Elaboration LCA milestone
  reviewed (4 criteria met, 2 carry-forward); recommendation **GO**. Seeded the
  Construction backlog in `docs/roadmap.md` — T-010..T-018, risk-front-loaded
  (T-010 AEAT `preproducción` PoC first to burn down residual R-03 with a running
  proof). Carry-forwards: AEAT PoC (O-1), current-calendar obligation check (O-2),
  pre-launch RGPD checklist (R-06). Next: `/openup-next` promotes T-010.

- **Iteration 8** (2026-06-15): T-009 complete — willingness-to-pay/pricing validation (PRICE-001). Founder ratified single flat plan ~7 €/mo (~70 €/yr) + free trial (no permanent free tier in v1), 12-month paying-accounts target **150–400** (narrow after beta), Verifactu deadline treated as uncertain/tracked. Closed Vision §5 paying-accounts TODO + scope §6 pricing item; R-04 reduced to a verifiable beta validation plan. Común-territory, build-direct context unchanged.

- **Iteration 7** (2026-06-15): T-008 complete — added REQ-004 (corrective + cancellation invoices) and detailed UC-004 (factura rectificativa) + UC-005 (Verifactu anulación), distinguishing correction of a valid invoice from voiding a record sent in error. Closed the S-5/D-1 scope gap; docs validate clean. Común-territory only (no TicketBAI, N-6).

- **Iteration 6** (2026-06-15): T-007 AEAT/Verifactu submission spike complete — founder ratified **BUILD direct, PoC-gated** (gateway fallback behind the same AD-3 interface), user-supplied certificate stored securely (O-1), Verifactu común-territory only / no TicketBAI in v1 (O-3). AD-3 resolved `proposed → accepted`; architecture notebook now has no open seams. O-2 (autónomo obligation timeline) carried to construction.

- **Iteration 5** (2026-06-15): T-006 complete — architecture notebook approved; founder resolved AD-5 (Python + Django) and AD-6 (PostgreSQL). AD-3 AEAT adapter remains open, deferred to the T-007 spike.

- **Iteration 4** (2026-06-15): Authored docs/scope.md (SCOPE-001) — ratified Vision §4/§6 into an explicit v1 scope (S-1..S-6) + non-goals (N-1..N-7), with three product-owner boundary decisions: corrective invoices in scope (D-1), B2B+B2C recipients (D-2), single-user/single-business account model (D-3). Follow-up: add a requirement for facturas rectificativas in Elaboration.

- **Iteration 3** (2026-06-15): Defined top use cases UC-001 (issue compliant invoice), UC-002 (submit to AEAT/Verifactu), UC-003 (manage client), each tracing from new draft requirements REQ-001..003 (← VIS-001). 7 instances validate; coverage clean (draft reqs carry no test expectation yet).

- **Iteration 2** (2026-06-15): Drafted docs/risk-list.md — 8 risks ranked by exposure, each with trigger + verifiable mitigation + owner; highest live exposures R-03 (AEAT integration) and R-04 (adoption/willingness to pay). Traces from vision §6–§7.

- **Iteration 1** (2026-06-15): Authored docs/vision.md for FacturaSimple via guided Q&A — compliance-first/Verifactu-native invoicing for autónomos & small pymes; north-star metric = time-to-first-invoice < 5 min. All 8 vision-rubric sections filled (TODOs: tech stack, paying-accounts target).
