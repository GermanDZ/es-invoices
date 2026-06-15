---
title: "AEAT/Verifactu submission — build-vs-buy decision (AD-3)"
created: "2026-06-15T12:45:00Z"
created_by: "openup-next (T-007, architect hat)"
status: processed
answered_by: "founder"
answered: "2026-06-15"
run_id: "T-007-iter6"
related_task: "T-007"
---

# Input Request — AEAT Submission Build-vs-Buy (AD-3)

## Context

**Iteration 6 (Elaboration), task T-007** — the time-boxed AEAT/Verifactu
submission spike (addresses **R-03**, the highest live technical exposure, and
resolves the open seam **AD-3** in the architecture notebook).

The spike research is **done and persisted** in
`docs/changes/T-007/design.md`. Headline findings:

- The target is the AEAT **VERI\*FACTU sending-mode web service** (SOAP/XML
  against public XSD, qualified-certificate auth, with a `preproducción`
  sandbox). Its public contract makes a direct **BUILD** *feasible, medium
  effort, and de-riskable inside a time box*.
- Record generation + hash-chaining + signing is **already core and in-house**
  (AD-2). So "buy a gateway" really means **paying a recurring per-invoice fee
  for a thin SOAP call we are mostly equipped to make** — unless the build PoC
  fails.
- Scored against the architecture's quality attributes/risks, the criteria
  **lean BUILD** (no per-invoice cost in a price-sensitive market — R-04; data
  stays in our EU stack — Q-3; coherent ownership of the core compliance path —
  AD-2), with **R-03 (integration risk)** the one strong pull toward BUY.

**Architect's recommendation:** **BUILD direct integration as the v1 target,
gated by a sandbox PoC**, keeping AD-3's interface so a gateway adapter can be
swapped in *if the PoC blows its time box* (exactly R-03's pre-agreed
mitigation — low-regret because the interface makes the choice cheap to
reverse).

This is brought to you (not decided by the architect) because it trades **your
engineering time vs cash** and sets a **recurring-cost structure that shapes
pricing/margins** — the same "only the founder can supply the deciding input"
reason AD-5/AD-6 were yours to make.

## Questions

### Q1: Build-vs-buy direction for AEAT submission (AD-3)
**Type**: multiple-choice
**Accepts**: one option

- [x] `BUILD direct, PoC-gated (recommended)` - Attempt the sandbox PoC; commit to
      direct integration if it clears the time box, else fall back to a gateway
      adapter behind the same AD-3 interface.
- [ ] `BUY a gateway from the start` - Integrate a third-party e-invoice/AEAT
      gateway now; accept the recurring per-document cost to offload R-03 entirely.
- [ ] `BUILD direct, unconditionally` - Commit to direct integration with no
      gateway fallback (highest control, highest R-03 exposure).

**Answer**: BUILD direct. Taken as the **PoC-gated** variant (the recommendation) —
keep AD-3's interface so a gateway adapter can be swapped in if the sandbox PoC
blows its time box.

### Q2: Certificate model (O-1 — shapes the adapter either way)
**Type**: multiple-choice
**Accepts**: one option

- [x] `User supplies their own AEAT certificate` - Each user uploads/holds their
      qualified cert; we store + use it (more RGPD/storage burden on us).
- [ ] `FacturaSimple submits on their behalf` - Act as colaborador social / use a
      sello de empresa to submit (less user friction; legal/agreement setup).
- [ ] `Not sure — needs investigation` - Treat O-1 as an open spike sub-task.

**Answer**: User supplies their own AEAT certificate; **we store it securely**
(encrypted at rest in our EU stack). Accepts the added RGPD/secure-storage burden
— a construction-phase requirement on the adapter + onboarding flow.

### Q3: Budget tolerance for a gateway, if the build path stalls
**Type**: text
**Example**: "Up to ~X€/month or ~X cents/invoice is acceptable", "No recurring per-invoice cost — must be build", "Whatever ships fastest"

If the build PoC blows its time box, what recurring cost (if any) would you
tolerate for a gateway fallback? This calibrates the fallback.

**Answer**: Defer — decide later. To be calibrated at build time, only if the
PoC actually stalls. Not load-bearing for this spike's decision.

### Q4: Anything else that should steer or veto the choice?
**Type**: text
**Example**: "I already hold a sello de empresa cert", "must support País Vasco TicketBAI in v1", "a specific provider is off the table"

Optional — existing certs, accounts, legal constraints, or a target segment
detail (e.g. foral territories) that changes the calculus.

**Answer**: No need to support País Vasco (TicketBAI). Confirms v1 is
común-territory (Verifactu) **only** — resolves spike Open Question O-3; TicketBAI
/ territorios forales stay out of v1 scope (consistent with N-6).

## Instructions for Respondent

1. Fill in the **Answer** section under each question (tick one box for the
   multiple-choice ones).
2. Change `status: pending` → `status: answered` in the frontmatter.
3. Save the file.
4. Re-run `/openup-next` — it will resume T-007, fold your decision into **AD-3**
   (resolve `proposed → accepted`), update the architecture notebook, and
   complete the task.
