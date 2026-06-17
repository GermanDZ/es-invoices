---
title: "T-010 — AEAT preproducción access (certificate + sandbox) to run the 3 proofs"
created: "2026-06-17T18:05:00Z"
created_by: "openup-next (loop)"
status: pending  # pending | answered | processed
run_id: "2026-06-17-T-010-openup-next"
related_task: "T-010"
---

# T-010 — AEAT preproducción access (certificate + sandbox) to run the 3 proofs

## Context

T-010 is the AEAT `preproducción` submission PoC — three proofs that gate the
BUILD-direct AD-3 decision and burn down residual R-03 before broad Construction
build. **Operations box 1 (scaffold) is done**: `poc/aeat-preproduccion/` is built
and structurally verified (`README.md`, `requirements.txt`, `config.py`, and
`proofs/proof{1,2,3}_*.py` skeletons that fail cleanly with `BLOCKED: not yet
wired` when no cert/endpoint is configured; secrets git-ignored). See
`docs/changes/T-010/handoff.md` for the full receiver brief.

**What's blocked:** the three proofs themselves (boxes 2–6) cannot be executed by
the autonomous loop. They require a **qualified certificate valid for AEAT
`preproducción`** and **live network access to the AEAT VERI\*FACTU SOAP
endpoint** — credentials and access only the founder can supply. The lane is
suspended on this request (`awaiting-input` in `docs/changes/T-010/plan.md`); a
later `/openup-next` resumes it automatically once this is answered.

## Questions

### Q1: Certificate for `preproducción`

**Type**: multiple-choice

**Question**: Which qualified certificate will the PoC use against AEAT
`preproducción`? (The harness code is identical either way — it reads the cert
from an env-injected local path; nothing is committed.)

- [ ] `fnmt-test` - An FNMT *test* certificate provisioned for `preproducción`
- [ ] `founder-real` - The founder's own qualified certificate, exercised against the sandbox
- [ ] `blocked-no-cert` - No certificate obtainable → R1 fails closed; trigger the AD-3 time-box / gateway-fallback path
- [ ] `other` - Other (specify below)

**Answer**: 
<!-- Fill your answer here -->


### Q2: Current `preproducción` WSDL/XSD endpoint URLs

**Type**: text

**Question**: What are the **current** `preproducción` VERI\*FACTU WSDL + XSD
URLs to use? Resolve these at run time — do NOT rely on the dates/URLs in the
T-007 spec, which have moved (T-007 carry-forward O-2). If you'd rather the
runner resolves them live, say so and leave the value as "resolve at run time".

**Example**: "WSDL: https://…/SistemaFacturacion/…?wsdl ; XSD: https://…/…xsd (or: resolve at run time)"

**Answer**: 
<!-- Fill your answer here -->


### Q3: If a proof blocks at the 2-session time box — AD-3 fallback

**Type**: multiple-choice

**Question**: If any of the three proofs cannot clear within the 2-session time
box, the pre-agreed back-out (R-03 mitigation) is to swap a **gateway provider
adapter** behind the same AD-3 interface. Do you pre-authorize triggering that
gateway-fallback decision at the time box, or should the runner raise a fresh
request for your call at that point?

- [ ] `raise-fresh` - Raise a new input-request with the specific blocker for a founder decision at the time box (default)
- [ ] `pre-authorize-fallback` - Pre-authorize the gateway-fallback path now; the runner records it without a second round-trip
- [ ] `other` - Other (specify below)

**Answer**: 
<!-- Fill your answer here -->


## Instructions

1. Fill in the **Answer** section for each question above.
2. For multiple-choice questions, check the chosen option with `[x]`.
3. Change `status:` in the frontmatter from `pending` to `answered`.
4. Save the file. The next `/openup-next` cycle resumes T-010 automatically
   (folds answers into the spec, removes `awaiting-input`, archives this request).
   - If you have the certificate + endpoint on hand, you can instead run the
     proofs directly per `docs/changes/T-010/handoff.md §2` and record outcomes
     in `docs/changes/T-010/design.md`.
</content>
</invoke>
