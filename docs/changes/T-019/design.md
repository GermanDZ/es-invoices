# T-019 — Design / completion notes

## Resolved blocking decision (Ambiguity Gate)

The roadmap row "Remove feature flag `AEAT_SUBMISSION_ENABLED` (T-014 fully rolled out)"
rested on a false premise: the gate is a **default-OFF safety kill-switch** that keeps
local/CI from making real, legally-effective AEAT submissions — not a rollout flag, which
a default-OFF gate can never be "fully rolled out" of. Product-owner decision
(2026-06-18, interactive): **repurpose, don't delete** — keep the kill-switch, rename it
to read as permanent infrastructure.

Chosen new name: `AEAT_SUBMISSION_LIVE` (truthy = this environment may send live records;
default OFF). Rejected `AEAT_SUBMISSION_KILL_SWITCH` because a "kill-switch" name inverts
the truthy semantics (off = killed) across every call site — an inversion-bug magnet.
Truthy=submit and default-OFF are preserved exactly; only the name + framing changed.

## Requirement grade vs diff (step 1a) — all ✅

1. ✅ Rename + default-OFF preserved — `config/settings.py:117`
   (`AEAT_SUBMISSION_LIVE = _env("AEAT_SUBMISSION_LIVE", "0") == "1"`); `FlagOffTests`
   (`@override_settings(AEAT_SUBMISSION_LIVE=False)`) green.
2. ✅ `submit_record` gates on new name, DISABLED outcome unchanged —
   `submission/services.py:49`; `test_disabled_short_circuits_and_writes_no_attempt` green.
3. ✅ `aeat_submit` refuses cleanly by the new name — `aeat_submit.py:28-30`.
4. ✅ Old name absent from live code/tests — `grep -rn AEAT_SUBMISSION_ENABLED --include='*.py'`
   (excl `docs/changes/archive`, `docs/agent-logs`) → zero matches.
5. ✅ Permanent framing in docs — `config/settings.py:106-116` comment + `submission/services.py`
   module/`submit_record` docstrings state the control is permanent, not rollout debt.
6. ✅ Suite green, unchanged counts — `python manage.py test` → 123 passed, 2 Postgres-gated
   skips (identical to iteration 17).

## Success Measure (step 1b)

`n/a` — internal config-contract rename, no user-facing surface, no telemetry. Verified
mechanically (R4 grep + green suite), not measured post-release. No read-back date.

## Rollout / flag-removal (step 4a)

**No flag-removal task is enqueued — intentionally.** This task does not introduce a flag;
it renames an existing **permanent** kill-switch and declares it permanent infrastructure.
Creating a removal follow-up would reintroduce the exact mischaracterization T-019 fixes.
The §Rollout section argues the not-a-rollout-flag case; rubric criterion 13 satisfied via
the permanent-control framing rather than a removal row.

## Deploy note

Env-var rename: deployments setting `AEAT_SUBMISSION_ENABLED=1` (production live submission)
must rename it to `AEAT_SUBMISSION_LIVE=1`. local/CI set nothing and stay default-OFF.
