---
id: T-019
title: Reframe AEAT submission kill-switch as permanent control (rename AEAT_SUBMISSION_ENABLED)
status: done
priority: medium
estimate: 0.5 session
plan: docs/roadmap.md#maintenance
depends-on: [T-014]
blocks: []
touches:
  - config/settings.py
  - submission/services.py
  - submission/management/commands/aeat_submit.py
  - submission/tests/test_services.py
  - invoicing/tests/test_corrective.py
last-synced: ""
---

# T-019 — Reframe AEAT submission kill-switch as permanent control

## Story

> **As a** maintainer of the FacturaSimple submission stack
> **I want** the AEAT live-submission gate to read unambiguously as permanent safety
>   infrastructure rather than a temporary rollout flag
> **So that** no future cleanup pass deletes the one control that stops dev/CI from
>   making real, legally-effective tax-authority submissions by accident.

INVEST check:
✅ Independent (touches only the submission gate name/framing) · ✅ Negotiable (exact
new name is open) · ✅ Valuable (removes a standing footgun in the backlog) ·
✅ Estimable (known call sites) · ✅ Small (rename + docs + tests) · ✅ Testable
(suite stays green; old name gone)

## Analysis Context

State the *why* the spec needs but the code can't show:
- **Domain.** Operational/config surface of the AEAT submission adapter (`submission`
  app, `config/settings.py`). The gate decides whether `submit_record` reaches the
  live tax authority or short-circuits to a `DISABLED` outcome.
- **Scope boundaries.** This task does **not** change submission logic, retry/pending
  degradation, cert handling, endpoints, or any use-case flow. It does **not** remove
  the gate (the original roadmap premise) — see the resolved blocking question below.
  It does **not** invert the truthy=submit semantics.
- **Definition of done.** The gate is renamed to a name that signals a permanent
  environment capability, its docstring/comment frames it as permanent (not debt), all
  call sites + tests + the management command use the new name, the old name appears
  nowhere in live code/tests, the full suite is green, and the roadmap row no longer
  describes a flag removal.

Resolved blocking question (Ambiguity Gate): the roadmap row T-019 ("Remove feature
flag `AEAT_SUBMISSION_ENABLED` — T-014 fully rolled out") rests on a false premise.
`AEAT_SUBMISSION_ENABLED` is a **default-OFF safety kill-switch** (`config/settings.py:106-112`:
"so local/CI never reach the tax authority by accident"), not a rollout flag — a
default-OFF gate is never "fully rolled out". Removing it would make every environment
(local/CI included) call the live AEAT unconditionally and break the `@override_settings`
tests. Product owner decision (2026-06-18): **repurpose, don't delete** — keep the
kill-switch, reframe it as permanent control.

> **Assumption:** new name is `AEAT_SUBMISSION_LIVE` (truthy = this environment may send
> live records; default OFF). Chosen over `AEAT_SUBMISSION_KILL_SWITCH`, which would
> invert semantics (off = killed) across every call site and invite inversion bugs.
> *(Vetoable at review.)*
> **Assumption:** truthy=submit semantics and default-OFF are preserved exactly; only
> the name and framing change. *(Vetoable at review.)*

## Requirements

1. The live-submission gate is renamed from `AEAT_SUBMISSION_ENABLED` to
   `AEAT_SUBMISSION_LIVE`, preserving truthy=submit semantics and the default-OFF value.
   - **Given** the env var `AEAT_SUBMISSION_LIVE` is unset **When** Django settings load
     **Then** `settings.AEAT_SUBMISSION_LIVE` is `False` (default OFF, identical to today).
   - **Given** `AEAT_SUBMISSION_LIVE=1` **When** settings load **Then** the value is `True`.
2. `submit_record` gates on the new name with unchanged behavior.
   - **Given** `AEAT_SUBMISSION_LIVE` is falsey **When** `submit_record(record)` is called
     **Then** it returns a `DISABLED` outcome, makes no network/cert call, and persists no
     `SubmissionAttempt` (same as before the rename).
3. The `aeat_submit` management command refuses cleanly when the gate is off, by the new name.
   - **Given** `AEAT_SUBMISSION_LIVE` is off **When** `manage.py aeat_submit <id>` runs
     **Then** it raises `CommandError` naming `AEAT_SUBMISSION_LIVE` and makes no submission.
4. The old name `AEAT_SUBMISSION_ENABLED` no longer appears in live code, settings, or tests.
   - **Given** the repo after this task **When** `grep -rn AEAT_SUBMISSION_ENABLED` runs over
     `*.py` (excluding `docs/changes/archive/` and audit logs) **Then** it returns no matches.
5. The settings comment/docstrings frame the gate as a **permanent** safety control, not
   temporary rollout debt, so it is not re-enqueued for removal.
   - **Given** a reader of `config/settings.py` and `submission/services.py` **When** they
     read the gate's documentation **Then** it states the control is permanent (no flag-removal
     follow-up implied).
6. The existing test suite remains green with the rename applied.
   - **Given** the renamed gate **When** `python manage.py test` runs **Then** the suite passes
     with the same pass/skip counts as before (116 green, Postgres-gated skips unchanged).

## Behavior Delta

How this task changes **existing product behavior** (Ring 1: `docs/`):

**Added** — none.

**Modified** — operational/config contract only:
- The env var that gates live AEAT submission is renamed `AEAT_SUBMISSION_ENABLED` →
  `AEAT_SUBMISSION_LIVE`. Deployments setting the old var must update it. No Ring-1
  use-case flow changes: UC-002 (`docs/use-cases/UC-002-submit-invoice-to-aeat.md`) does
  not surface the gate — its precondition ("AEAT submission credentials/certificate are
  configured", §preconditions) is unaffected.

**Removed** — none. (The gate itself is **retained**; only its name/framing change. The
roadmap's "remove flag" framing is withdrawn — see Rollout.)

## Entities

- **AEAT submission gate** (modified) — `config/settings.py:106-122` (`AEAT_SUBMISSION_ENABLED` → `AEAT_SUBMISSION_LIVE`)
- **submit_record** (modified) — `submission/services.py:48`
- **aeat_submit command** (modified) — `submission/management/commands/aeat_submit.py:28-32`
- **submission tests** (modified) — `submission/tests/test_services.py:27,30`
- **corrective tests** (modified) — `invoicing/tests/test_corrective.py:24`
- **UC-002** (read-only) — `docs/use-cases/UC-002-submit-invoice-to-aeat.md`

## Approach

A pure rename-plus-reframe: swap the identifier `AEAT_SUBMISSION_ENABLED` for
`AEAT_SUBMISSION_LIVE` everywhere it is read or overridden, keeping truthy=submit and
default-OFF unchanged so no logic moves. The substantive change is documentation intent:
the settings comment and `submission/services.py` docstring are rewritten to describe a
**permanent** environment safety gate (one that *must* exist forever to protect dev/CI),
explicitly not a rollout flag, so `/openup-complete-task`'s flag-removal-follow-up
machinery is not re-triggered. Mirrors the existing config-read-at-startup pattern.

## Structure

**Add:**
- (none)

**Modify:**
- `config/settings.py` — rename the setting + rewrite the §AEAT SUBMISSION comment to frame it as permanent
- `submission/services.py` — gate name in `submit_record` + module docstring framing
- `submission/management/commands/aeat_submit.py` — gate check + help text + module docstring
- `submission/tests/test_services.py` — `@override_settings` keys + ENABLED dict key
- `invoicing/tests/test_corrective.py` — ENABLED dict key
- `docs/use-cases/UC-002-submit-invoice-to-aeat.md` — only if it cites the old name (it does not today; touch only if needed)

**Do not touch:**
- `submission/services.py` retry/pending/persist logic — behavior is frozen; only the gate identifier changes
- `AEAT_ENV` / `AEAT_ENDPOINT` / `AEAT_SUBMISSION_MAX_RETRIES` / `AEAT_SUBMISSION_TIMEOUT` — separate settings, out of scope
- `docs/changes/archive/**`, `docs/agent-logs/**`, `docs/status-notes/**` — historical records keep the old name as written

## Operations

- [x] Rename `AEAT_SUBMISSION_ENABLED` → `AEAT_SUBMISSION_LIVE` in `config/settings.py` and rewrite the §AEAT SUBMISSION comment to frame it as a permanent safety kill-switch (not rollout debt); confirm default stays OFF.
- [x] Update the gate read in `submission/services.py` (`submit_record`) and its module docstring to the new name + permanent framing.
- [x] Update `submission/management/commands/aeat_submit.py` — settings check, `CommandError` message, help/docstring — to the new name.
- [x] Update test overrides/keys in `submission/tests/test_services.py` and `invoicing/tests/test_corrective.py` to `AEAT_SUBMISSION_LIVE`.
- [x] (tester) Run `grep -rn AEAT_SUBMISSION_ENABLED --include='*.py'` excluding `docs/changes/archive` and audit logs — expect zero matches; then run the full test suite and confirm it is green with unchanged pass/skip counts.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs/conventions.md` (if exists) — project conventions
- `config/settings.py` `_env(...)` helper — the config-read-at-startup pattern this rename preserves

> Reference, don't copy.

## Safeguards

- **Token / size budget.** Small mechanical change; touched files ≤ 6, no new files.
- **Reversibility.** Single-commit rename — revert restores the old name; no data/migration involved.
- **No-go zones.** Submission logic, retry/pending degradation, cert handling, endpoints,
  and the default-OFF / truthy=submit semantics must not change. The gate must **not** be
  removed (that was the rejected interpretation).
- **Safety invariant.** After the change, local/CI must still default to NOT calling the
  live AEAT (gate default OFF) — the whole point of retaining it.

## Success Measures

n/a — internal config-contract rename with no user-facing surface and no telemetry to
read back. Success is mechanical and verified at completion (Requirement 4 grep + green
suite), not measured post-release.

## Rollout

- **Flagged?** n/a in the rollout sense — this task does not introduce a flag; it
  **renames an existing permanent kill-switch** and explicitly declares it permanent
  infrastructure. No flag-removal follow-up is created (creating one would reintroduce
  the exact mischaracterization this task fixes).
- **Reaching environments.** The change is an env-var rename. Deployments that set
  `AEAT_SUBMISSION_ENABLED=1` (production live submission) must rename it to
  `AEAT_SUBMISSION_LIVE=1` at deploy time; local/CI set nothing and stay default-OFF.
  No `environments:` chain is defined in `docs/project-config.yaml`, so the relevant
  states are local (OFF) and production (operator-set).
- **Kill-switch behavior (retained).** Setting the gate falsey makes `submit_record`
  short-circuit to a `DISABLED` outcome with no network/cert call and no persisted
  attempt — unchanged from today; this is the safety property being preserved, not added.

## Verification

- `grep -rn "AEAT_SUBMISSION_ENABLED" --include='*.py'` (excluding `docs/changes/archive`
  and `docs/agent-logs`) returns no matches.
- `python manage.py test` passes with unchanged counts (116 green + Postgres-gated skips).
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-019/plan.md` exits 0.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.
