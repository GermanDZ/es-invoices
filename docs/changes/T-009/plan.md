---
id: T-009
task_id: T-009
title: "Willingness-to-pay / pricing validation"
status: suspended
track: quick
phase: elaboration
traces-from: [VIS-001, R-04, SCOPE-001]
touches: [docs/pricing-validation.md, docs/changes/T-009/, docs/input-requests/, docs/vision.md, docs/scope.md]
depends-on: [T-005]
awaiting-input: docs/input-requests/2026-06-15-pricing-and-paying-target.md
---

# T-009 — Willingness-to-pay / pricing validation

> Elaboration lane addressing **R-04** (low adoption / weak willingness to pay —
> highest live *business* exposure) and closing the **paying-accounts target**
> (Vision §5 TODO) + the **pricing** open item (scope §6). This is a
> research/decision lane — its deliverable is an evidence-based pricing
> hypothesis + a validation plan + a founder decision, **not** code.

## Goal

Produce a willingness-to-pay & pricing validation artifact that gives the founder
a benchmarked price band, candidate pricing models, funnel-derived
paying-accounts target options, and a verifiable validation plan that discharges
R-04 — then obtain the founder's pricing + target decisions and fold them back
into the Vision and scope.

## Deliverable

- `docs/pricing-validation.md` (PRICE-001) — the analysis artifact.
- A founder input-request for the four decisions only the founder can make.
- (On resume) Vision §5 + scope §6 updated with the decisions; artifact → agreed.

## Operations

- [x] (analyst) Self-brief from Vision §5/§6, risk-list R-04, scope §6.
- [x] (analyst) Gather competitor-pricing benchmarks + Verifactu deadline context.
- [x] (analyst) Author `docs/pricing-validation.md`: market context, benchmark,
      WTP hypothesis, candidate models + recommendation, funnel-derived target
      options, R-04 validation plan.
- [x] (analyst) Raise founder input-request (pricing model, price, free-tier,
      paying-accounts target, steering input) and suspend the lane.
- [ ] (analyst) **[awaiting founder]** Fold answers into Vision §5 (set target)
      and scope §6 (mark pricing decided); set PRICE-001 `status: agreed`.
- [ ] (analyst) Complete the task via `/openup-complete-task`.

## Notes

- Resumes via `/openup-next` step 0 once the input-request is answered
  (`status: answered`).
- WTP figures in the artifact are benchmarks/hypotheses; only beta + interviews
  (validation plan §6) convert them to measured facts — that conversion is the
  R-04 mitigation, owned by the Product Owner, executed in/after construction.
