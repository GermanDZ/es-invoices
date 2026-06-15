# T-006 Handoff — Architecture Notebook + Tech Stack ADR

**Status:** in-progress (paused on async input) · **Branch:** design/T-006-architecture-notebook · **For:** next session / founder
**Last commit:** bbd6826 — chore(log): record agent run events *(architecture notebook authored this session, commit pending this exit)*

## 1. Acceptance criteria
> T-006 goal: "Architecture notebook + tech stack ADR" (roadmap, Elaboration).
- [x] `docs/architecture-notebook.md` exists, traces from VIS-001, passes `check-docs.py`.
- [x] Key architectural decisions recorded as ADRs (AD-1..AD-6) with forcing constraint + rejected alternatives.
- [x] Constraints + quality attributes specified (Spain-only, EU residency/RGPD, solo-team; Q-1..Q-6).
- [x] EU data-residency decision made (AD-4 accepted — European cloud provider).
- [ ] **Tech stack ADR resolved (AD-5)** — DEFERRED to founder; notebook is `status: draft` until answered. **This is the one open AC blocking completion.**

## 2. How to exercise it (verify)
1. `python3 scripts/check-docs.py` → `OK — no failures` (frontmatter + traceability).
2. Read `docs/architecture-notebook.md` §3 — confirm AD-1..AD-6 each state the constraint that forces them + rejected alternatives.
3. Confirm AD-5 + AD-6 + §7 mark the stack as open and point at the input-request.

## 3. Troubleshooting
> Friction hit this session, for the next operator.
- **Sibling worktree + gate-edits hook** → the `gate-edits.py` hook is anchored to `$CLAUDE_PROJECT_DIR` (main repo), so a sibling worktree's `.openup/state.json` is invisible to it and all `docs/` edits are blocked. **Fix:** for sessions rooted in the main repo, use an in-place branch (not a sibling worktree) so state + gate share one tree.
- **Standard track blocked artifact edits** → `gate-edits` requires `plan_persisted` on the `standard` track; artifact tasks (no REASONS-Canvas plan.md) must run on the **`quick` track** (precedent: T-002..T-005 all quick). **Fix:** re-init state with `--track quick --force`.
- **`status: proposed` rejected by check-docs** → allowed doc statuses are `draft|approved|implemented|verified|obsolete`. Use `draft` for an open decision.

## 4. Open questions
- **AD-5 — application tech stack (language + framework).** Deferred to founder expertise. Raised as input-request `docs/input-requests/2026-06-15-tech-stack-decision.md` (status: pending). Criteria the architecture imposes: mature XML + XAdES signing, PDF generation, EU-hostable, founder fluency.
- **AD-6 — datastore** recommended PostgreSQL; confirm once AD-5 lands (some stacks bundle a default).
- **AD-3 adapter (build-vs-buy)** — intentionally deferred to **T-007** (AEAT submission spike); not a T-006 blocker.

## Resume path
Iteration state for T-006 remains **active** (`.openup/state.json`, quick track). When the founder answers the input-request (sets `status: answered`), re-run `/openup-next`: step 1a resumes T-006 → fold answers into AD-5/AD-6 → flip notebook to `approved` → `/openup-complete-task`.
