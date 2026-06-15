# T-009 Handoff — Willingness-to-pay / pricing validation

**Status:** suspended (awaiting founder input) · **Branch:** docs/T-009-pricing-wtp-validation · **For:** Founder / Product Owner (then next `/openup-next` cycle)
**Last commit:** (none yet on branch — committed by this handoff exit; base 4df2e87)

## 1. Acceptance criteria
> What "done" means. From plan.md.
- [x] `docs/pricing-validation.md` (PRICE-001) authored: market context, competitor benchmark, WTP hypothesis, candidate models + recommendation, funnel-derived target options, R-04 validation plan.
- [x] Founder input-request raised; lane suspended (board shows `suspended`).
- [ ] **[awaiting founder]** Pricing model + price + free-tier + paying-accounts target decided (input-request Q1–Q5).
- [ ] On resume: Vision §5 target set, scope §6 marked pricing-decided, PRICE-001 → `status: agreed`.
- [ ] Task completed via `/openup-complete-task`.

## 2. How to exercise it (verify / resume)
> Concrete steps.
1. Read `docs/pricing-validation.md` — the analysis the decision rests on.
2. Answer `docs/input-requests/2026-06-15-pricing-and-paying-target.md`: fill each **Answer**, tick the multiple-choice boxes, set frontmatter `status: pending` → `answered`, save.
3. Re-run `/openup-next` → it resumes T-009 (step 0 detects the answered request), folds answers into Vision §5 + scope §6, finalizes PRICE-001, and completes the task.
4. Verify board state any time: `python3 scripts/openup-board.py refresh` (T-009 shows `suspended` until answered).

## 3. Troubleshooting
> Failure modes hit during the work.
- **Worktree was based on stale `main`** (5 commits behind; T-008's completed work was unmerged) → founder chose to ff-merge `docs/T-008-...` into `main`, then the T-009 worktree was recreated off updated `main`. Resolved before any authoring.
- **`openup-scribe` subagent unavailable** in this environment → project-status, logs, and this handoff written directly by the running agent (values still author-determined). No impact on artifacts.

## 4. Open questions
> Handed to the founder (these ARE the input-request).
- Q1 Pricing model (A single-flat+trial / B freemium / C tiered).
- Q2 Price point for the paid plan.
- Q3 Free trial vs. permanent free tier (+ what it caps).
- Q4 Committed 12-month paying-accounts target (closes Vision §5 TODO).
- Q5 Steering input — esp. the **Verifactu deadline assumption** (1 Jul 2026 per RD 254/2025 vs. proposed 1 Jul 2027 prórroga), which swings Q1/Q3.
- Analyst recommendation on record: single flat ~7 €/mo + trial; add a capped free tier only if the deadline defers; tiering out of v1.
