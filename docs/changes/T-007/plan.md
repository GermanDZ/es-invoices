---
id: T-007
task_id: T-007
title: "AEAT/Verifactu submission spike (build-vs-buy)"
status: in-progress
track: quick
phase: elaboration
traces-from: [R-03, AD-3, UC-002]
touches: [docs/architecture-notebook.md, docs/changes/T-007/, docs/input-requests/]
depends-on: [T-005, T-006]
---

# T-007 — AEAT/Verifactu submission spike (build-vs-buy)

> Time-boxed Elaboration spike addressing **R-03** (highest live technical
> exposure) and resolving the open seam **AD-3** in the architecture notebook.
> This is a research/decision lane: its deliverable is a documented spike result
> + a build-vs-buy ADR decision, not production code.

## Goal

Validate the feasibility of AEAT/Verifactu submission and produce a build-vs-buy
recommendation, so AD-3's adapter (`proposed`) can be resolved to `accepted`.

## Acceptance criteria

- [x] Submission target system characterised (Verifactu sending mode, transport,
      auth, sandbox) — `design.md §1–§2`.
- [x] Feasibility of direct BUILD assessed with explicit PoC proof-points —
      `design.md §2`.
- [x] Build-vs-buy evaluated against the architecture's quality attributes/risks,
      with a recommendation — `design.md §3–§4`.
- [x] **Founder ratifies the build-vs-buy direction** (input request) — the one
      load-bearing decision the architect cannot make alone (cost/eng-time trade,
      like AD-5/AD-6). Decided: **BUILD direct, PoC-gated**; user-supplied cert
      (stored securely); común-territory only (no TicketBAI). See archived request.
- [x] AD-3 resolved (`proposed → accepted`) in `docs/architecture-notebook.md`
      §3/§7 with the chosen adapter; T-007 completed.

## Operations

- [x] (analyst/architect) Characterise the Verifactu submission system + boundaries.
- [x] (architect) Assess BUILD feasibility; name the sandbox PoC proof-points.
- [x] (architect) Build-vs-buy analysis vs Q-attributes/risks; write recommendation.
- [x] (architect) Raise founder ratification as an input request; suspend the lane.
- [x] (architect) Fold the ratified decision into AD-3; update architecture
      notebook; complete the task.

## Out of scope

- Implementing the adapter (construction phase).
- TicketBAI / foral territories, Facturae/FACe, B2B *Crea y Crece* e-invoicing
  (see `design.md §1`).
