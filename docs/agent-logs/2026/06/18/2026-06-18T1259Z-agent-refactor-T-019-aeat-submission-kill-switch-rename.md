# Agent Run Log — T-019

- **Task**: T-019 — Reframe AEAT submission kill-switch as permanent control
- **Branch**: refactor/T-019-aeat-submission-kill-switch-rename
- **Phase**: construction (Maintenance backlog) · **Iteration**: 18 · **Track**: standard
- **Start**: 2026-06-18T12:53:47Z · **End**: 2026-06-18T12:59:22Z
- **Role hats**: developer → tester (solo, sequential)

## Commits

- `6bc2624` docs(T-019): promote lane — author spec, board-visible [T-019]
- `2b39a45` refactor(T-019): rename AEAT_SUBMISSION_ENABLED -> AEAT_SUBMISSION_LIVE [T-019]

## Files changed

- `config/settings.py` — renamed gate + reframed §AEAT SUBMISSION comment (permanent control)
- `submission/services.py` — gate read + module/`submit_record` docstrings
- `submission/management/commands/aeat_submit.py` — check, `CommandError`, help/docstring
- `submission/tests/test_services.py` — `@override_settings` keys + ENABLED dict
- `invoicing/tests/test_corrective.py` — ENABLED dict key
- `docs/changes/T-019/plan.md` — spec (REASONS Canvas) + ticked Operations
- `docs/changes/T-019/design.md` — blocking-decision record + requirement grade

## Key decisions

- **Blocking ambiguity resolved by product owner**: the roadmap's "remove flag" premise was
  false — `AEAT_SUBMISSION_ENABLED` is a default-OFF safety kill-switch, not rollout debt.
  Decision: **repurpose, don't delete**.
- Renamed to `AEAT_SUBMISSION_LIVE` (truthy=submit, default OFF preserved). Rejected
  `…_KILL_SWITCH` to avoid inverting semantics across call sites.
- **No flag-removal follow-up enqueued** — by design; the gate is permanent infrastructure.

## Result

- All 6 spec requirements graded ✅ against the diff (recorded in `design.md`).
- Full suite: 123 passed, 2 Postgres-gated skips (unchanged from iteration 17).
- Old identifier `AEAT_SUBMISSION_ENABLED` absent from all `*.py`.
- Write-fence ✅ (7 files in-lane); check-docs ✅ (11 instances).
