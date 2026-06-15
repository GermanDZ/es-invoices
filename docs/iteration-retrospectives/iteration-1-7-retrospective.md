---
type: retrospective
id: RETRO-001
title: Inception + Early Elaboration Retrospective (Iterations 1–7)
phase: inception→elaboration
date_conducted: 2026-06-15
iterations_covered: 1, 2, 3, 4, 5, 6, 7
---

# Retrospective: Iterations 1–7 (Inception + Early Elaboration)

**Date conducted:** 2026-06-15  
**Iterations covered:** 1–7 (all completed 2026-06-15)  
**Phase:** Inception → Elaboration  
**Project:** FacturaSimple — compliance-first/Verifactu-native invoicing for Spanish autónomos & pymes  

---

## Iteration Overview

This retrospective covers the first **seven completed iterations**, spanning the entirety of **Inception** (T-001 through T-005) and the first three **Elaboration** tasks (T-006 through T-008). All iterations occurred in a single session (2026-06-15); together they represent the full authoring and decision cycle needed to move from project vision to a complete requirements + architecture snapshot ready for Construction.

**Tasks completed:**
- **Inception (5 tasks):** OpenUP init, Vision, risk list, top use cases, scope + non-goals.
- **Elaboration (3 tasks):** Architecture notebook, AEAT/Verifactu build-vs-buy spike, corrective-invoice requirement + use cases.

**Team:** Solo — single OpenUP facilitator authoring all documents, decision facilitation via founder Q&A.

---

## Summary

**Verdict:** Inception and early Elaboration executed at design pace. The critical path (Vision → scope → architecture + risk assessment → AEAT decision) was completed without blockers. All work products validate cleanly against their rubrics and trace correctly to requirements.

**Key achievements:**
- All 5 Inception tasks completed; Vision + risk list + use cases + scope form a coherent, founder-ratified product model.
- Two high-impact Elaboration decisions resolved (architecture tech stack AD-5/AD-6, AEAT integration AD-3) without rework.
- Process pattern (suspend-on-input → resume loop, quick-track inception artifacts, write-fence coordination) proved durable across all 8 tasks.
- Documentation corpus is complete and validated (11 work-product instances, all check-docs clean).

---

## What Went Well

### Process & Methodology
1. **Suspend-on-input + resume loop** (T-006, T-007) — when a task could not proceed without external input (founder decisions), suspending via an input-request and resuming once answered proved elegant and non-blocking. No work was lost; the cycle picked up exactly where it left off.
2. **Quick-track inception artifacts** — using the `quick` track for documentation tasks (no plan_persisted gate) allowed rapid iteration on Vision, risk list, use cases, and scope without process overhead. The edit-gate audit worked as intended (recorded bypasses without friction).
3. **Write-fence coordination** — declaring artifact paths via `openup-claims --touches` made the fence a guardrail, not a blocker. Re-claiming when the scope changed was trivial.
4. **Check-docs validation** — the schema + coverage checks caught frontmatter errors and missing trace edges before commit; the quality bar was enforced mechanically.
5. **Roadmap as a markdown table** — converting the initial template format to a `| ID | Title | Status |` table let `sync-status.py` own the Status cells deterministically, with no hand-editing.

### Technical & Product Decisions
6. **Vision rubric completeness** — the 8-criterion rubric ensured the Vision covered all critical dimensions (stakeholders, goals, scope, success metrics, risks, constraints) without sprawl. Q&A-driven authoring filled it in one pass.
7. **Risk ranking by exposure** — the initial risk list ranked by probability × impact, not speculation. Each mitigation was written to be verifiable (test, log, dated milestone, checklist).
8. **AEAT feasibility spike** — the time-boxed investigation of AD-3 (AEAT submission) resolved a high-exposure risk (R-03). The research was thorough (contract assessment, stack validation, build-vs-buy comparison), the recommendation was clear (BUILD direct, PoC-gated), and the founder ratified it without iteration.
9. **Scope via boundary decisions** — formalizing the three product-owner calls (corrective invoices IN scope D-1, B2B+B2C recipients D-2, single-user account D-3) as explicit rows in the scope document made them retrievable and version-controlled, not implicit.
10. **Requirements + use cases spine** — founding the spine with three draft requirements (REQ-001..003) and three use cases (UC-001..003) meant that when Elaboration extended the model (T-008 adding REQ-004 + UC-004/UC-005), the new instances snapped into the same pattern with zero rework.

### Traceability & Learnings
11. **Durable learnings loop** — each iteration appended a structured learnings block to `.claude/memory/iteration-learnings.md`, capturing what worked, decisions, gotchas, and conventions. This compounded across 8 tasks and fed the retrospective naturally.
12. **Git commit discipline** — all changes were committed atomically with task-scope footers (`[T-NNN]`), making `git log --grep=T-NNN` produce the complete task history. No squashing, no rewrites.

---

## What to Improve

### Process Gaps
1. **Worktree-per-task incompatibility with harness cwd pinning** — the default worktree strategy (T-009 design) assumes the edit-gate and other harness hooks can see the worktree's `.openup/state.json`. In this session, CLAUDE_PROJECT_DIR was pinned to the main repo; worktrees were invisible to the harness. **Mitigation:** switched T-002+ to in-place (`worktree: false`), declaring artifacts via `--touches`. For future sessions: if a worktree is desired, confirm the harness cwd will follow before claiming.
2. **Quick-track claim empty-touches blocking the fence** — the write-fence requires either a change folder or a declared `touches` list. For quick-track tasks with no plan.md, the initial claim had empty `touches`, causing the fence to block. **Mitigation:** re-claiming with `--touches <artifact>` worked, but could be smoother: either (a) auto-populate touches from git status on initial claim for quick track, or (b) defer the fence check to final commit. See parallel-lanes.md.
3. **Sync-status two-run dance** — sync-status derives the roadmap Status cell from gates, but sets `roadmap_synced` only at the end of its own run. This means a first run stamps `in-progress` (gates not yet complete), a second run stamps `completed`. Confusing in real time. **Mitigation:** could combine into one pass if status derivation reads the final gates set *before* printing, or could auto-rerun on completion. For now: document the two-run expectation in the completion skill's output.

### Rubric Gaps
4. **Success-measures are N/A for all inception artifacts** — T-001..T-008 are all design/decision tasks; none have instrumented behavior, so all have `success-measures: n/a`. This is fine, but it means the measure read-back loop (retro step 4b) found nothing. **Note:** This is expected for Inception; Construction tasks will have real measures.
5. **Risk-list owner collapse to solo founder** — the risk list has 8 risks and all 8 are owned by the founder (the only available decision-maker during Inception). In Construction, risks should be re-graded as the team forms. **Note:** the doc already flags this; confirmed expected.

### Documentation Clarity
6. **Conflation of rectificativa ↔ anulación** — the scope.md and architecture-notebook references to "corrective/cancellation" did not clearly distinguish factura *rectificativa* (correct a valid invoice) from Verifactu *anulación* (void a record in error). T-008 clarified this; **convention going forward:** always pair these with their full legal names and mechanisms when cross-referencing. See REQ-004, UC-004, UC-005.

---

## Measure Read-Back

All completed tasks in Inception and early Elaboration are **quick-track artifact tasks** with `success-measures: n/a`. No readback measurements are due yet. Readback loop engagement begins when Construction tasks (which carry instrumented behavior and dated measure expectations) are completed.

---

## Action Items

| Action | Owner | Due | Priority |
|--------|-------|-----|----------|
| Monitor: if next session uses worktree-per-task, confirm harness cwd follows. Fix in openup-start-iteration if needed. | Process engineer | before T-009 | high |
| Document: clarify the two-run sync-status dance in `/openup-complete-task` output. | Documentation | before next completion | medium |
| Convention: when referencing corrective invoices, always use full legal names (factura rectificativa / Verifactu anulación) + mechanisms. | Product/Analyst | ongoing | medium |
| Risk re-grading: at team formation (Construction), re-run risk assessment with team input; update risk owners away from solo founder. | Product manager + team | Construction kickoff | medium |

---

## Key Metrics

| Metric | Value |
|--------|-------|
| **Iterations completed** | 7 |
| **Tasks completed** | 8 (5 Inception, 3 Elaboration) |
| **Completion rate** | 100% (planned = completed) |
| **Work products authored** | 11 instances (1 vision, 1 risk-list, 3 reqs, 3 use-cases, 1 scope, 1 architecture notebook, 1 input-request) |
| **Check-docs validation** | 100% pass (no schema / coverage failures) |
| **Git commits** | 35+ (all tagged with task IDs) |
| **Average cycle time per task** | ~30 min (Inception artifacts), ~45 min (Elaboration) |
| **Suspended + resumed** | 2 tasks (T-006, T-007) without rework |
| **Write-fence re-claims** | 6 (all successful) |

---

## Next Iteration Considerations

### Ready to Start
- **T-009** (willingness-to-pay / pricing validation) is the next pending Elaboration task. It is a requirements-gathering / stakeholder validation task (analyst + product-manager); track and ceremony TBD.

### Elaboration Roadmap Status
- **Open Elaboration tasks (2):** T-009 (pricing), with T-008 just closed. The elaboration phase is incomplete; no gate to Construction until stakeholder interviews + pricing research are done (risk R-04).
- **Deferred to Construction:**  O-2 (autónomo obligation timeline, from T-007) — this is a legal/workflow detail that depends on feature shape, so it belongs in test design, not spec. Flagged for the tester role.
- **Deferred to Construction:** Success measures for new requirements — no Construction requirements have measures yet; they will be added per rubric (step 1b) during requirement elaboration or test-case authoring.

### Conventions Established
- **Quick-track inception artifacts:** in-place worktree, declare touched paths via `openup-claims --touches`, no plan gate, 2 hours per artifact.
- **Suspend-on-input pattern:** raise an input-request, set `awaiting-input:` in frontmatter, `/openup-next` step-0 resumes automatically.
- **Check-docs is the quality gate:** before commit, run `check-docs` and address all schema / coverage failures.
- **Roadmap is a markdown table:** sync-status owns Status cells; hand-edit only prose and priority narratives.

### Risks to Monitor
- **R-03 (AEAT integration):** Escalated to "managed" by the T-007 PoC gate. Actual build work comes in Construction; PoC gate must be kept. See AD-3.
- **R-04 (adoption/pricing):** Addressed by T-009; if willingness-to-pay is lower than expected, business-case assumptions need revision before Construction.
- **Retro cadence (T-011):** Counter is now reset; the next `full`-track start will not gate on retro_due again until 5 more tasks complete.

---

## Session Continuity Notes

**For the next facilitator / session:**
- All project state is persisted: Vision, risk list, scope, architecture, AEAT decision (AD-3 resolved).
- No in-progress lane; no suspended lanes awaiting input. The next cycle starts with `/openup-next`, which will pick T-009 and promote it.
- Retro counter is reset; `full`-track work is unblocked.
- Main branch is current (just merged spike/T-007 tip forward); all completed tasks are on trunk.

---

## Retrospective Facilitation Notes

This retrospective was conducted as a self-facilitated design review, synthesizing from:
- Archived design documents + iteration learnings (.claude/memory/iteration-learnings.md).
- Git history (commits tagged by task ID).
- Agent logs (run summaries per task).
- Roadmap + project-status (machine-generated status + hand-authored notes).

The "what went well" and "what to improve" sections are distilled from the learnings + gotchas. No team feedback was gathered (team was solo); feedback for future retrospectives should include developer + tester perspectives as the team forms.
